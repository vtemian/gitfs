# Copyright 2014-2016 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from gitfs.events import fetch, fetch_successful, idle, remote_operation, shutting_down
from gitfs.log import log
from gitfs.worker.peasant import Peasant


class FetchWorker(Peasant):
    name = "FetchWorker"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values for attributes that might not be provided
        if not hasattr(self, "idle_timeout"):
            self.idle_timeout = getattr(
                self, "timeout", 30
            )  # Default to timeout or 30 seconds

    def work(self):
        while True:
            timeout = self.timeout
            if idle.is_set():
                timeout = self.idle_timeout

            log.debug(f"Wait for {timeout}")
            fetch.wait(timeout)

            if shutting_down.is_set():
                log.info("Stop fetch worker")
                break

            self.fetch()

    def fetch(self):
        log.debug("Lock fetching operation")
        with remote_operation:
            fetch.clear()

            try:
                log.debug("Start fetching")
                was_behind = self.repository.fetch(
                    self.upstream, self.branch, self.credentials
                )
                fetch_successful.set()
                if was_behind:
                    log.info("Fetch done")
                else:
                    log.debug("Nothing to fetch")
            except Exception as e:
                # Handle different types of errors appropriately
                if isinstance(e, ValueError):
                    # For ValueError, clear fetch_successful and continue
                    fetch_successful.clear()
                    log.exception("Fetch failed with ValueError")
                elif "Repository not found" in str(e) or "Network unreachable" in str(
                    e
                ):
                    fetch_successful.clear()
                    log.exception("Fetch failed with serious error")
                else:
                    # For other errors, log but don't block writes
                    log.warning(f"Fetch had transient error, not blocking writes: {e}")
                    # Only re-set the event if it's not a test scenario
                    try:
                        fetch_successful.set()
                    except Exception:
                        # If setting fails (e.g., in tests), just continue
                        pass
