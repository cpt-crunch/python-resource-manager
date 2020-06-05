# Copyright 2015 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility for managing folders via the Cloud Resource Manager API."""

from google.cloud.exceptions import NotFound


class Folder(object):
    """Folders are containers for your work on Google Cloud Platform.

    .. note::

        A :class:`Folder` can also be created via
        :meth:`Client.new_folder() \
        <google.cloud.resource_manager.client.Client.new_folder>`

    To manage labels on a :class:`Folder`::

        >>> from google.cloud import resource_manager
        >>> client = resource_manager.Client()
        >>> folder = client.new_folder('purple-spaceship-123')
        >>> folder.labels = {'color': 'purple'}
        >>> folder.labels['environment'] = 'production'
        >>> folder.update()

    See
    https://cloud.google.com/resource-manager/reference/rest/v1beta1/folders

    :type name: str
    :param name: The globally unique ID of the folder.

    :type client: :class:`google.cloud.resource_manager.client.Client`
    :param client: The Client used with this folder.

    :type display_name: str
    :param display_name: The display display_name of the folder.

    :type labels: dict
    :param labels: A list of labels associated with the folder.
    """

    def __init__(self, client, name=None, display_name=None, parent=None):
        self._client = client
        self.name = name
        self.display_name = display_name
        self.status = None
        self.parent = parent

    def __repr__(self):
        return "<Folder: %r (%r)>" % (self.display_name, self.name)

    @classmethod
    def from_api_repr(cls, resource, client):
        """Factory:  construct a folder given its API representation.

        :type resource: dict
        :param resource: folder resource representation returned from the API

        :type client: :class:`google.cloud.resource_manager.client.Client`
        :param client: The Client used with this folder.

        :rtype: :class:`google.cloud.resource_manager.folder.Folder`
        :returns: The folder created.
        """
        folder = cls(name=resource["name"], client=client)
        folder.set_properties_from_api_repr(resource)
        return folder

    def set_properties_from_api_repr(self, resource):
        """Update specific properties from its API representation."""
        self.name = resource.get("name")

        if "parent" in resource:
            self.parent = resource["parent"]

        if "lifecycleState" in resource:
            self.status = resource["lifecycleState"]

    @property
    def path(self):
        """URL for the folder (ie, ``'/folders/purple-spaceship-123'``)."""
        return "/%s" % (self.name)

    def _require_client(self, client):
        """Check client or verify over-ride.

        :type client: :class:`google.cloud.resource_manager.client.Client` or
                      ``NoneType``
        :param client: the client to use.  If not passed, falls back to the
                       ``client`` stored on the current folder.

        :rtype: :class:`google.cloud.resource_manager.client.Client`
        :returns: The client passed in or the currently bound client.
        """
        if client is None:
            client = self._client
        return client

    def create(self, client=None):
        """API call:  create the folder via a ``POST`` request.

        See
        https://cloud.google.com/resource-manager/reference/rest/v1beta1/folders/create

        :type client: :class:`google.cloud.resource_manager.client.Client` or
                      :data:`NoneType <types.NoneType>`
        :param client: the client to use.  If not passed, falls back to
                       the client stored on the current folder.
        """
        client = self._require_client(client)

        data = {"name": self.name, "displayName": self.display_name}
        query_params = {"parent": self.parent}
        resp = client._connection_v2.api_request(
            method="POST", path="/folders", data=data, query_params=query_params
        )
        self.set_properties_from_api_repr(resp)
        return resp

    def reload(self, client=None):
        """API call:  reload the folder via a ``GET`` request.

        This method will reload the newest metadata for the folder. If you've
        created a new :class:`Folder` instance via
        :meth:`Client.new_folder() \
        <google.cloud.resource_manager.client.Client.new_folder>`,
        this method will retrieve folder metadata.

        .. warning::

            This will overwrite any local changes you've made and not saved
            via :meth:`update`.

        See
        https://cloud.google.com/resource-manager/reference/rest/v1beta1/folders/get

        :type client: :class:`google.cloud.resource_manager.client.Client` or
                      :data:`NoneType <types.NoneType>`
        :param client: the client to use.  If not passed, falls back to
                       the client stored on the current folder.
        """
        client = self._require_client(client)

        # We assume the folder exists. If it doesn't it will raise a NotFound
        # exception.
        resp = client._connection_v2.api_request(method="GET", path=self.path)
        self.set_properties_from_api_repr(resp)

    def exists(self, client=None):
        """API call:  test the existence of a folder via a ``GET`` request.

        See
        https://cloud.google.com/resource-manager/reference/rest/v1beta1/folders/get

        :type client: :class:`google.cloud.resource_manager.client.Client` or
                      :data:`NoneType <types.NoneType>`
        :param client: the client to use.  If not passed, falls back to
                       the client stored on the current folder.

        :rtype: bool
        :returns: Boolean indicating existence of the folder.
        """
        client = self._require_client(client)

        try:
            # Note that we have to request the entire resource as the API
            # doesn't provide a way tocheck for existence only.
            client._connection_v2.api_request(method="GET", path=self.path)
        except NotFound:
            return False
        else:
            return True

    def update(self, client=None):
        """API call:  update the folder via a ``PUT`` request.

        See
        https://cloud.google.com/resource-manager/reference/rest/v1beta1/folders/update

        :type client: :class:`google.cloud.resource_manager.client.Client` or
                      :data:`NoneType <types.NoneType>`
        :param client: the client to use.  If not passed, falls back to
                       the client stored on the current folder.
        """
        client = self._require_client(client)

        data = {"display_name": self.display_name, "parent": self.parent}

        resp = client._connection_v2.api_request(method="PUT", path=self.path, data=data)
        self.set_properties_from_api_repr(resp)

    def delete(self, client=None, reload_data=False):
        """API call:  delete the folder via a ``DELETE`` request.

        See
        https://cloud.google.com/resource-manager/reference/rest/v1beta1/folders/delete

        This actually changes the status (``lifecycleState``) from ``ACTIVE``
        to ``DELETE_REQUESTED``.
        Later (it's not specified when), the folder will move into the
        ``DELETE_IN_PROGRESS`` state, which means the deleting has actually
        begun.

        :type client: :class:`google.cloud.resource_manager.client.Client` or
                      :data:`NoneType <types.NoneType>`
        :param client: the client to use.  If not passed, falls back to
                       the client stored on the current folder.

        :type reload_data: bool
        :param reload_data: Whether to reload the folder with the latest
                            state. If you want to get the updated status,
                            you'll want this set to :data:`True` as the DELETE
                            method doesn't send back the updated folder.
                            Default: :data:`False`.
        """
        client = self._require_client(client)
        client._connection_v2.api_request(method="DELETE", path=self.path)

        # If the reload flag is set, reload the folder.
        if reload_data:
            self.reload()

    def undelete(self, client=None, reload_data=False):
        """API call:  undelete the folder via a ``POST`` request.

        See
        https://cloud.google.com/resource-manager/reference/rest/v1beta1/folders/undelete

        This actually changes the folder status (``lifecycleState``) from
        ``DELETE_REQUESTED`` to ``ACTIVE``.
        If the folder has already reached a status of ``DELETE_IN_PROGRESS``,
        this request will fail and the folder cannot be restored.

        :type client: :class:`google.cloud.resource_manager.client.Client` or
                      :data:`NoneType <types.NoneType>`
        :param client: the client to use.  If not passed, falls back to
                       the client stored on the current folder.

        :type reload_data: bool
        :param reload_data: Whether to reload the folder with the latest
                            state. If you want to get the updated status,
                            you'll want this set to :data:`True` as the DELETE
                            method doesn't send back the updated folder.
                            Default: :data:`False`.
        """
        client = self._require_client(client)
        client._connection_v2.api_request(method="POST", path=self.path + ":undelete")

        # If the reload flag is set, reload the folder.
        if reload_data:
            self.reload()

    def get_folder(self, client=None, name=None):
        """API call:  get the folder via a GET method

        See
        https://cloud.google.com/resource-manager/reference/rest/v1beta1/folders/create

        :type client: :class:`google.cloud.resource_manager.client.Client` or
                      :data:`NoneType <types.NoneType>`
        :param client: the client to use.  If not passed, falls back to
                       the client stored on the current folder.
        """
        client = self._require_client(client)

        resp = client._connection_v2.api_request(
            method="GET", path="/" + name
        )
        self.set_properties_from_api_repr(resp)
        return resp

    def get_iam_folder(self, client=None, name=None):
        """API call:  get the iam policy folder via a POST method

        See
        https://cloud.google.com/resource-manager/reference/rest/v1beta1/folders/create

        :type client: :class:`google.cloud.resource_manager.client.Client` or
                      :data:`NoneType <types.NoneType>`
        :param client: the client to use.  If not passed, falls back to
                       the client stored on the current folder.
        """

        client = self._require_client(client)

        resp = client._connection_v2.api_request(
            method="POST", path="/" + name + "/:getIamPolicy"
        )
        self.set_properties_from_api_repr(resp)
        return resp
