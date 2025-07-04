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


from collections import namedtuple
from io import TextIOWrapper
from unittest.mock import MagicMock, call, patch

from pygit2 import GIT_CHECKOUT_FORCE

from gitfs.merges.accept_mine import AcceptMine


Commit = namedtuple("Commit", ["hex", "message", "id"])


class TestAcceptMine:
    def test_create_local_copy(self):
        mocked_repo = MagicMock()
        mocked_branch = MagicMock()
        mocked_commit = MagicMock()

        mocked_branch.target.id = "local_commit"
        mocked_repo.branches.local.get.return_value = mocked_branch
        mocked_repo.__getitem__.return_value = mocked_commit
        mocked_repo.create_branch.return_value = "branch"

        mine = AcceptMine(mocked_repo)
        assert mine._create_local_copy("old_branch", "new_branch") == "branch"

        mocked_repo.create_branch.assert_called_once_with("new_branch", mocked_commit)

    def test_create_remote_copy(self):
        mocked_repo = MagicMock()
        mocked_branch = MagicMock()
        mocked_commit = MagicMock()

        mocked_branch.target.id = "remote_commit"
        mocked_repo.branches.remote.return_value = mocked_branch
        mocked_repo.__getitem__.return_value = mocked_commit
        mocked_repo.create_branch.return_value = "branch"

        mine = AcceptMine(mocked_repo)
        assert (
            mine._create_remote_copy("old_branch", "upstream", "new_branch") == "branch"
        )

        mocked_repo.create_branch.assert_called_once_with("new_branch", mocked_commit)
        mocked_repo.checkout.assert_has_calls([call(mocked_repo.lookup_reference.return_value, strategy=GIT_CHECKOUT_FORCE)])

        asserted_ref = "refs/heads/new_branch"
        mocked_repo.lookup_reference.assert_called_once_with(asserted_ref)

    def test_solve_conflicts_we_deleted_the_file(self):
        mocked_repo = MagicMock()
        mocked_file = MagicMock()

        mocked_file.path = "simple_path"

        def conflicts():
            yield None, mocked_file, None

        mine = AcceptMine(mocked_repo)
        mine.solve_conflicts(conflicts())

        mocked_repo.index.remove.assert_has_calls(
            [call("simple_path", 2), call("simple_path", 1)]
        )

    def test_solve_conflicts_they_deleted_the_file(self):
        mocked_repo = MagicMock()
        mocked_file = MagicMock()

        mocked_file.path = "simple_path"

        def conflicts():
            yield None, None, mocked_file

        mine = AcceptMine(mocked_repo)
        mine.solve_conflicts(conflicts())

        mocked_repo.index.add.assert_called_once_with("simple_path")

    def test_solve_conflicts_both_update_a_file(self):
        mocked_theirs = MagicMock()
        mocked_ours = MagicMock(id="id", path="path")
        mocked_full = MagicMock(return_value="full_path")
        mocked_repo = MagicMock(_full_path=mocked_full)

        mocked_repo.get().data = "data"

        def conflicts():
            yield None, mocked_theirs, mocked_ours

        mock_path = "gitfs.merges.accept_mine.open"
        with patch(mock_path, create=True) as mocked_open:
            mocked_file = MagicMock(spec=TextIOWrapper)
            mocked_open.return_value = mocked_file

            mine = AcceptMine(mocked_repo)

            mine.solve_conflicts(conflicts())

            mocked_full.assert_called_once_with("path")
            mocked_open.assert_called_once_with("full_path", "w")
            mocked_repo.get.assert_has_calls([call("id")])
            mocked_open().__enter__().write.assert_called_once_with("data")
            mocked_repo.index.add.assert_called_once_with("path")

    def test_merging_strategy(self):
        mocked_repo = MagicMock()
        mocked_copy = MagicMock()
        mocked_remote_copy = MagicMock()
        mocked_reload = MagicMock()
        mocked_diverge = MagicMock()
        mocked_solve = MagicMock()
        mocked_ref = MagicMock()
        mocked_find_commits = MagicMock()

        mocked_ref.target = "target"
        mocked_diverge.first_commits = [Commit(1, "message", 1)]
        mocked_repo.index.conflicts = "conflicts"
        mocked_repo.lookup_reference.return_value = mocked_ref
        mocked_repo.commit.return_value = "new_commit"
        mocked_repo.find_diverge_commits = mocked_find_commits
        mocked_reload.return_value = "reload"
        mocked_find_commits.return_value = mocked_diverge
        mocked_copy.return_value = "local_copy"
        mocked_remote_copy.return_value = "remote_copy"

        mine = AcceptMine(mocked_repo, author="author", committer="committer")

        mine._create_local_copy = mocked_copy
        mine._create_remote_copy = mocked_remote_copy
        mine.reload_branch = mocked_reload
        mine.solve_conflicts = mocked_solve

        mine.__call__("local_branch", "remote_branch", "upstream")

        mocked_copy.assert_called_once_with("local_branch", "merging_local")
        mocked_remote_copy.assert_called_once_with(
            "remote_branch", "upstream", "merging_remote"
        )
        mocked_find_commits.assert_called_once_with("local_copy", "remote_copy")
        mocked_repo.checkout.assert_has_calls([
            call("refs/heads/merging_remote", strategy=GIT_CHECKOUT_FORCE),  # In merge method
            call("refs/heads/merging_remote", strategy=GIT_CHECKOUT_FORCE),  # In merge loop
            call("refs/heads/local_branch", strategy=GIT_CHECKOUT_FORCE)     # In clean_up method
        ])
        mocked_repo.merge.assert_called_once_with(1)
        mocked_solve.assert_called_once_with(mocked_repo.index.conflicts)

        # The actual calls include chained .delete() calls from clean_up method
        # We need to check the complete call sequence including the chained calls
        expected_mock_calls = [
            call("refs/heads/merging_remote"),  # In merge method for commit
            call("refs/heads/merging_remote"),  # At end of merge method
            call("refs/heads/merging_local"),   # In clean_up method
            call().delete(),                    # Chained .delete() on merging_local ref
            call("refs/heads/merging_remote"),  # In clean_up method
            call().delete(),                    # Chained .delete() on merging_remote ref
        ]
        mocked_repo.lookup_reference.assert_has_calls(expected_mock_calls)
        mocked_repo.commit.assert_called_once_with(
            "merging: message", "author", "committer", ref="refs/heads/merging_remote", parents=["target", 1]
        )
        # create_reference is called twice: once for the commit, once to update local branch
        expected_create_calls = [
            call("refs/heads/merging_remote", "new_commit", force=True),  # In merge loop
            call("refs/heads/local_branch", "target", force=True),        # At end of merge method
        ]
        mocked_repo.create_reference.assert_has_calls(expected_create_calls)
        assert mocked_repo.state_cleanup.call_count == 1
        assert mocked_ref.delete.call_count == 2
