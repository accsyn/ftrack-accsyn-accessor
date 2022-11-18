# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os
import logging

from ftrack_api.accessor.disk import DiskAccessor
from ftrack_api.data import FileWrapper
from ftrack_api.exception import (
    AccessorOperationFailedError,
    AccessorUnsupportedOperationError,
    AccessorResourceInvalidError,
    AccessorResourceNotFoundError,
    AccessorContainerNotEmptyError,
    AccessorParentResourceNotFoundError,
)

logger = logging.getLogger('ftrack_accsyn_accessor.AccsynAccessor')


class AccsynFileWrapper(FileWrapper):
    @property
    def path(self):
        return self._path

    def __init__(self, file, path):
        self._path = path
        super(AccsynFileWrapper, self).__init__(file)

    def close(self):
        '''(Override) The file have been written locally, initiate accsyn transfer.'''
        logger.info('File "{}" written, syncing with accsyn'.format(self.path))

        # TODO: Locate sync job


class AccsynAccessor(DiskAccessor):
    """Provide accsyn location access."""

    def __init__(self, accsyn_session, prefix=None):
        """Initialise location accessor.

        Uses the server credentials specified by *host*, *password*, *port* and *password*
        to create a sftp connection.

        If specified, *folder* indicates the subfolder where assets are stored
        """
        super(AccsynAccessor, self).__init__(prefix=prefix)
        self._accsyn_session = accsyn_session
        logger.info('Initialised accsyn accessor')

    def open(self, resource_identifier, mode="rb"):
        """(Override)"""
        if self.is_container(resource_identifier):
            raise AccessorResourceInvalidError(
                resource_identifier=resource_identifier,
                message="Cannot open a directory: {resource_identifier}",
            )
        return AccsynFileWrapper(
            super(AccsynAccessor, self).open(resource_identifier, mode=mode),
            self.get_filesystem_path(resource_identifier),
        )
