"""
Abstraction of root resources and drive resources. In the API, a "*dir" call accesses a directory, a "*file" call
accesses a file, and a "*item" call accesses either a directory or a file.
https://github.com/OneDrive/onedrive-api-docs#root-resources
"""

import json

import requests

from . import errors
from . import facets
from . import items
from . import options


class DriveRoot:
    """
    An entry point to get associated drives.
    """

    def __init__(self, account):
        """
        :param onedrive_d.api.accounts.PersonalAccount | onedrive_d.api.accounts.BusinessAccount account:
        """
        self.account = account

    def get_all_drives(self):
        """
        :rtype dict[str, DriveObject]: a dictionary of all drives with keys being drive IDs.
        """
        uri = self.account.client.API_URI + '/drives'
        while True:
            try:
                request = self.account.session.get(uri)
                if request.status_code != requests.codes.ok:
                    raise errors.OneDriveError(request.json())
                drives = {}
                for d in request.json()['value']:
                    drives[d['id']] = DriveObject(self, d)
                return drives
            except errors.OneDriveTokenExpiredError:
                self.account.renew_tokens()

    def get_default_drive(self, list_children=True):
        return self.get_drive(list_children=list_children)

    def get_drive(self, drive_id=None, list_children=True):
        """
        :param str | None drive_id: (Optional) ID of the target Drive. Use None to get default Drive.
        """
        uri = self.account.client.API_URI + '/drive'
        if drive_id is not None:
            uri = uri + 's/' + drive_id
        if list_children:
            uri = uri + '?expand=children'
        while True:
            try:
                request = self.account.session.get(uri)
                if request.status_code != requests.codes.ok:
                    raise errors.OneDriveError(request.json())
                return DriveObject(self, request.json())
            except errors.OneDriveTokenExpiredError:
                self.account.renew_tokens()


class DriveObject:
    """
    Abstracts a specific Drive resource.
    """

    def __init__(self, root, data):
        """
        :param onedrive_d.api.drives.OneDriveRoot root: The parent root object.
        :param dict[str, T] data: The deserialized Drive dictionary.
        """
        self.root = root
        self._data = data
        self.drive_uri = root.account.client.API_URI + '/drives/' + data['id']

    @property
    def id(self):
        """
        Return the drive ID.
        :rtype: str
        """
        return self._data['id']

    @property
    def type(self):
        """
        Return a string representing the drive's type. {'personal', 'business'}
        :rtype: str
        """
        return self._data['driveType']

    @property
    def quota(self):
        return facets.QuotaFacet(self._data['quota'])

    def refresh(self):
        """
        Refresh metadata of the drive object.
        """
        new_drive = self.root.get_drive(self.id)
        self.__dict__.update(new_drive.__dict__)
        del new_drive

    def get_item_uri(self, item_id=None, item_path=None):
        uri = self.drive_uri
        if item_id is not None:
            uri = uri + '/items/' + item_id
        elif item_path is not None:
            uri = uri + '/root:/' + item_path
        else:
            uri = uri + '/root'
        return uri

    def get_root_dir(self, list_children=True):
        uri = self.drive_uri + '/root'
        if list_children:
            uri = uri + '?expand=children'
        request = self.root.account.session.get(uri)
        return request.json()

    def search_item(self):
        pass

    def get_all_items(self):
        pass

    def get_item(self, item_id=None, item_path=None, list_children=True):
        """
        Retrieve the metadata of an item from OneDrive server.
        :param str item_id:  ID of the item. Required if item_path is None.
        :param str item_path: Path to the item relative to drive root. Required if item_id is None.
        :rtype:
        """
        uri = self.get_item_uri(item_id, item_path)
        if list_children:
            uri = uri + '?expand=children'
        request = self.root.account.session.get(uri)
        return request.json()

    def create_dir(self, name, parent_id=None, parent_path=None,
                   conflict_behavior=options.NameConflictBehavior.DEFAULT):
        """
        Create a new directory under the specified parent directory.
        :param str name: Name of the new directory.
        :param str parent_id: (Optional) ID of the parent directory item.
        :param str parent_path: (Optional) Path to the parent directory item.
        :param str conflict_behavior: (Optional) What to do if name exists. One value from options.nameConflictBehavior.
        :return onedrive_d.api.items.OneDriveItem: The newly created directory item.
        """
        data = {
            'name': name,
            'folder': {},
            '@name.conflictBehavior': conflict_behavior
        }
        uri = self.get_item_uri(parent_id, parent_path)
        response = self.root.account.session.post(uri, data=json.dumps(data))
        if response.status_code != requests.codes.created:
            raise errors.OneDriveError(response.json())
        return items.OneDriveItem(response.json())

    def upload_file(self):
        pass

    def delete_item(self):
        pass

    def patch_item(self):
        pass

    def move_item(self):
        pass

    def copy_item(self):
        pass

    def get_thumbnail(self):
        pass

    def get_changes(self):
        pass

    def get_special_dir(self, name):
        pass