import asyncio
import docker
import logging
import tempfile
import os
from aegis.monitors.resource_tracker import ResourceTracker

logger = logging.getLogger("Aegis-Sandbox")

class EphemeralSandbox:
    def __init__(self, image_name: str = "aegis-sandbox", timeout: int = 10, tracker: ResourceTracker = None):
        # I'm using the default docker environment. 
        # Make sure Docker Desktop is actually running or this will throw an error immediately.
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            self.client = None
        self.image_name = image_name
        self.timeout = timeout
        self.container = None
        self.tracker = tracker

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # I'm being extremely careful about cleanup here.
        # If a container stays alive, it could keep eating CPU in the background.
        if self.container:
            try:
                self.container.remove(force=True)
                logger.debug("Ephemeral container destroyed.")
            except Exception as e:
                logger.error(f"Failed to destroy container: {e}")

    async def run_code(self, code: str, honeypots: dict = None, safe_network: bool = False) -> dict:
        """
        This is where the magic happens. I'm spinning up a completely isolated Linux
        container just to run a single script. 
        """
        if not self.client:
            return {"status": "error", "error": "Docker client not initialized."}

        # NEW in V2.0: Network Interception Logic
        # If safe_network is enabled, we inject the interceptor at the start of the script.
        final_code = code
        if safe_network:
            try:
                with open('monitors/network_proxy.py', 'r') as f:
                    interceptor_logic = f.read()
                
                # We inject the initialization call.
                # We pass the honeypot secrets to the interceptor so it can block them.
                forbidden_secrets = []
                if honeypots:
                    for content in honeypots.values():
                        for line in content.split('\n'):
                            if '=' in line:
                                forbidden_secrets.append(line.split('=')[-1].strip())

                injection = (
                    f"{interceptor_logic}\n"
                    f"AegisNetworkInterceptor(forbidden_strings={forbidden_secrets}).install()\n"
                    f"# --- AI GENERATED CODE BELOW ---\n"
                )
                final_code = injection + code
            except Exception as e:
                logger.error(f"Failed to inject network interceptor: {e}")

        # I'm writing the AI's code to a temp file on the host and then mounting it 
        # as read-only inside the container. This is way safer than passing strings.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w') as tmp:
            tmp.write(final_code)
            tmp_path = tmp.name

        # NEW in V2.0: Dynamic Honeypot Mounting
        # We mount fake versions of sensitive files into the container.
        mounts = {tmp_path: {'bind': '/sandbox/script.py', 'mode': 'ro'}}
        honeypot_files = []
        
        if honeypots:
            for filename, content in honeypots.items():
                # Create a temporary file for each honeypot asset
                h_tmp = tempfile.NamedTemporaryFile(delete=False, mode='w')
                h_tmp.write(content)
                h_tmp.close()
                mounts[h_tmp.name] = {'bind': f'/sandbox/{filename}', 'mode': 'ro'}
                honeypot_files.append(h_tmp.name)

        try:
            logger.info(f"Spinning up Hardened Docker container (Honeypots: {len(honeypot_files)})...")
            # V3.0 HARDENING:
            # 1. Drop ALL kernel capabilities (prevent raw syscalls)
            # 2. Use a custom user (already in Dockerfile)
            # 3. Read-only root filesystem (optional, but good)
            self.container = self.client.containers.run(
                self.image_name,
                command=f"python /sandbox/script.py",
                volumes=mounts,
                detach=True,
                network_disabled=not safe_network,
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=50000,
                cap_drop=["ALL"],           # Drop all Linux capabilities
                security_opt=["no-new-privileges"], # Prevent privilege escalation
            )

            # Asynchronous wait loop so we don't block the whole orchestrator.
            for _ in range(self.timeout):
                self.container.reload()
                
                # I'm capturing telemetry while the container is alive.
                if self.tracker and self.container.status == 'running':
                    self.tracker.capture(self.container)
                
                if self.container.status == 'exited':
                    break
                await asyncio.sleep(1)
            
            # If it's still running after the timeout, it's probably an infinite loop. Kill it.
            if self.container.status != 'exited':
                self.container.kill()
                return {"status": "error", "error": "Execution timed out. Potential infinite loop."}

            # Grab the logs (stdout/stderr) so we can see what the code actually did.
            logs = self.container.logs().decode('utf-8')
            result = self.container.wait()
            
            if result['StatusCode'] == 0:
                return {"status": "success", "output": logs}
            else:
                return {"status": "error", "error": logs}

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            # Cleanup the temp file. Don't want to leave junk on my disk.
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            # Cleanup honeypot temp files
            for h_path in honeypot_files:
                if os.path.exists(h_path):
                    os.remove(h_path)
