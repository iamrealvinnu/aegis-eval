import asyncio
import docker
import logging
import tempfile
import os
from monitors.resource_tracker import ResourceTracker

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

    async def run_code(self, code: str) -> dict:
        """
        This is where the magic happens. I'm spinning up a completely isolated Linux
        container just to run a single script. 
        """
        if not self.client:
            return {"status": "error", "error": "Docker client not initialized."}

        # I'm writing the AI's code to a temp file on the host and then mounting it 
        # as read-only inside the container. This is way safer than passing strings.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w') as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            logger.info("Spinning up isolated Docker container...")
            # I've hardcapped the resources here. 256MB and 50% CPU.
            # If the model tries to "thread-bomb" us, these limits will catch it.
            self.container = self.client.containers.run(
                self.image_name,
                command=f"python /sandbox/script.py",
                volumes={tmp_path: {'bind': '/sandbox/script.py', 'mode': 'ro'}},
                detach=True,
                network_disabled=True,      # This is the most important part: NO internet for the AI.
                mem_limit="256m",           # Keep it lean
                cpu_period=100000,
                cpu_quota=50000             # Cap at 0.5 CPU
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
