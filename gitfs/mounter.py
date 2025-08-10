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


import argparse
import os
import resource
import sys

from pygit2 import Keypair, RemoteCallbacks, UserPass

from gitfs import __version__
from gitfs.router import Router
from gitfs.routes import prepare_routes
from gitfs.utils import Args
from gitfs.worker import CommitQueue, FetchWorker, SyncWorker
from gitfs.log import log

from gitfs.fuse_compat import get_fuse_module, is_fuse3, get_fuse_version, FUSE


def parse_args(parser):
    parser.add_argument("remote_url", help="repo to be cloned")
    parser.add_argument("mount_point", help="where the repo should be mount")
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + __version__
    )
    parser.add_argument(
        "-o",
        help="other options: repo_path, user, "
        "group, branch, max_size, max_offset, "
        "fetch_timeout, merge_timeout, ssh_user",
    )

    return Args(parser)


def get_credentials(args):
    if args.password:
        credentials = UserPass(args.username, args.password)
    else:
        credentials = Keypair(args.ssh_user, args.ssh_key + ".pub", args.ssh_key, "")
    return RemoteCallbacks(credentials=credentials)


def prepare_components(args):
    commit_queue = CommitQueue()

    credentials = get_credentials(args)

    try:
        # setting router
        router = Router(
            remote_url=args.remote_url,
            mount_path=args.mount_point,
            current_path=args.current_path,
            history_path=args.history_path,
            repo_path=args.repo_path,
            branch=args.branch,
            user=args.user,
            group=args.group,
            max_size=args.max_size * 1024 * 1024,
            max_offset=args.max_size * 1024 * 1024,
            commit_queue=commit_queue,
            credentials=credentials,
            ignore_file=args.ignore_file,
            hard_ignore=args.hard_ignore,
        )
    except KeyError as error:
        sys.stderr.write(
            f"Can't clone reference origin/{args.branch} from remote {args.remote_url}: {error}\n"
        )
        raise error

    # register all the routes
    routes = prepare_routes(args)
    router.register(routes)

    # setup workers
    merge_worker = SyncWorker(
        args.committer_name,
        args.committer_email,
        args.committer_name,
        args.committer_email,
        commit_queue=commit_queue,
        repository=router.repo,
        upstream="origin",
        branch=args.branch,
        repo_path=router.repo_path,
        timeout=args.merge_timeout,
        credentials=credentials,
        min_idle_times=args.min_idle_times,
    )

    fetch_worker = FetchWorker(
        upstream="origin",
        branch=args.branch,
        repository=router.repo,
        timeout=args.fetch_timeout,
        credentials=credentials,
        idle_timeout=args.idle_fetch_timeout,
    )

    merge_worker.daemon = True
    fetch_worker.daemon = True

    router.workers = [merge_worker, fetch_worker]

    return merge_worker, fetch_worker, router


def start_fuse():
    parser = argparse.ArgumentParser(prog="GitFS")
    args = parse_args(parser)

    # Log FUSE version information
    fuse_version = get_fuse_version()
    fuse_type = "FUSE 3" if is_fuse3() else "FUSE 2"
    log.info(f"Using {fuse_type} (version {fuse_version})")

    fuse_module = get_fuse_module()
    if hasattr(fuse_module, "_libfuse_path"):
        log.info(f"FUSE library: {fuse_module._libfuse_path}")

    merge_worker, fetch_worker, router = prepare_components(args)

    if args.max_open_files != -1:
        resource.setrlimit(
            resource.RLIMIT_NOFILE, (args.max_open_files, args.max_open_files)
        )

    # ready to mount it
    fuse_kwargs = {
        "foreground": args.foreground,
        "fsname": args.remote_url,
        "subtype": "gitfs",
        "rw": True,  # Explicitly set read-write mode for FUSE3
    }

    # Configure mount options based on FUSE version
    if is_fuse3():
        log.info("Using FUSE 3 mount options")
        # Add default_permissions to let FUSE3 handle permissions properly
        fuse_kwargs["default_permissions"] = True

        # Only add allow_other if not running as root
        # In FUSE3, allow_other and allow_root are mutually exclusive
        if args.allow_root and os.geteuid() == 0:
            fuse_kwargs["allow_root"] = True
        elif args.allow_other:
            fuse_kwargs["allow_other"] = True
    else:
        log.info("Using FUSE 2 mount options")
        # FUSE2 allows both allow_other and allow_root
        if args.allow_root:
            fuse_kwargs["allow_root"] = True
        if args.allow_other:
            fuse_kwargs["allow_other"] = True

    # Workaround for mfusepy issue where it looks for operations on FUSE object
    if is_fuse3():
        # Create a wrapped FUSE class that provides missing methods
        class FUSE3Wrapper(FUSE):
            def __init__(self, operations, *args, **kwargs):
                # Add FUSE3 operations to self so mfusepy can find them
                for op_name in ["copy_file_range", "lseek"]:
                    if hasattr(operations, op_name):
                        # Create a method that delegates to operations
                        def make_delegator(name):
                            def delegator(*args, **kwargs):
                                return getattr(operations, name)(*args, **kwargs)

                            return delegator

                        setattr(self, op_name, make_delegator(op_name))

                super().__init__(operations, *args, **kwargs)

        FUSE3Wrapper(router, args.mount_point, **fuse_kwargs)
    else:
        FUSE(router, args.mount_point, **fuse_kwargs)


if __name__ == "__main__":
    start_fuse()
