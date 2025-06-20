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


from gitfs.views import CommitView, CurrentView, HistoryView, IndexView


# TODO: replace regex with the strict one for the Historyview
# -> r'^/history/(?<date>(19|20)\d\d[-](0[1-9]|1[012])[-](0[1-9]|[12][0-9]|3[01]))/',
def prepare_routes(args):
    routes = []

    routes.append(
        (
            r"^/%s/(?P<date>\d{4}-\d{1,2}-\d{1,2})/(?P<time>\d{2}-\d{2}-\d{2})-(?P<commit_sha1>[0-9a-f]{10})"
            % args.history_path,
            CommitView,
        )
    )
    routes.append(
        (r"^/%s/(?P<date>\d{4}-\d{1,2}-\d{1,2})" % args.history_path, HistoryView)
    )
    routes.append((r"^/%s" % args.history_path, HistoryView))

    if "/" == args.current_path:
        routes.append((r"^/", CurrentView))
    else:
        routes.append((r"^/%s" % args.current_path, CurrentView))
        routes.append((r"^/", IndexView))

    return routes
