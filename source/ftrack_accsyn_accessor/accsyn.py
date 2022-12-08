# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os
import logging
import datetime

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

from ftrack_accsyn_accessor._version import __version__

logger = logging.getLogger('ftrack_accsyn_accessor.AccsynAccessor')

#
# class AccsynFileWrapper(FileWrapper):
#
#
#
#     def __init__(self, file, location_id, share, path, client, ftrack_session, accsyn_session):
#         self._location_id = location_id
#         self._share = share
#         self._path = path
#         self._client = client
#         self._ftrack_session = ftrack_session
#         self._accsyn_session = accsyn_session
#         super(AccsynFileWrapper, self).__init__(file)
#
#     def close(self):
#         '''(Override) The file have been written locally, initiate accsyn transfer.'''
#         logger.info('File "{}" written to local mapped share "{}", syncing with accsyn'.format(self.path, self.share))
#
#         # Find out upload location
#         upload_location = self.accsyn_session.get_setting(name='upload_location', integration='ftrack',
#                                               data={'location_id': self.location_id})
#
#         # TODO: Locate sync job


class AccsynAccessor(DiskAccessor):
    """Provide accsyn location access."""

    @property
    def location_id(self):
        return self._location_id

    @property
    def share(self):
        return self._share

    @property
    def path(self):
        return self._path

    @property
    def client(self):
        return self._client

    @property
    def ftrack_session(self):
        return self._ftrack_session

    @property
    def accsyn_session(self):
        return self._accsyn_session

    def __init__(
        self,
        location_id,
        share,
        client,
        ftrack_session,
        accsyn_session,
        prefix=None,
    ):
        """Initialise location accessor.

        Uses the server credentials specified by *host*, *password*, *port* and *password*
        to create a sftp connection.

        If specified, *folder* indicates the subfolder where assets are stored
        """
        super(AccsynAccessor, self).__init__(prefix=prefix)
        self._location_id = location_id
        self._share = share
        self._client = client
        self._ftrack_session = ftrack_session
        self._accsyn_session = accsyn_session

        # Register location with client
        logger.info('Registering accsyn client with location')
        self._accsyn_session.integration(
            'ftrack',
            'client_register',
            {'client': self.client['id'], 'location': self.location_id},
        )

        logger.info('Registering to "ftrack.location.component-added" events')
        ftrack_session.event_hub.subscribe(
            'topic=ftrack.location.component-added and data.location_id={}'.format(
                location_id
            ),
            self.component_added,
        )
        logger.info(
            'Initialised accsyn accessor v{} (location: {}, share: {}, client: {})'.format(
                __version__, self._location_id, self._share, self._client
            )
        )

    def component_added(self, event):
        '''
        <Event {'id': '98d4871190ef4d5ba6b4bf53efdca22d', 'data': {'component_id': '61e29ad4-4f4e-4f20-9171-05fa075baa79', 'location_id': 'c26a5ce7-ca32-452a-8c04-4750246a72da'}, 'topic': 'ftrack.location.component-added', 'sent': None, 'source': {'id': '84e5abd6d3c94c59979e70c9e4a76ed4', 'user': {'username': 'henrik.norin@ftrack.com'}}, 'target': '', 'in_reply_to_event': None}>

        :param event:
        :return:
        '''

        try:
            # Fetch component and path
            location = self.ftrack_session.query(
                'Location where id={}'.format(self.location_id)
            ).one()
            component = self.ftrack_session.query(
                'Component where id={}'.format(event['data']['component_id'])
            ).one()
            resource_identifier = location.get_resource_identifier(component)

            logger.info(
                'Component {} file "{}" written to local mapped share "{}" @ location "{}", syncing with accsyn'.format(
                    component['id'],
                    resource_identifier,
                    self.share,
                    self.location_id,
                )
            )

            location = self.ftrack_session.query(
                'Location where id={}'.format(self.location_id)
            ).one()

            # Query the destination location for upload
            upload_location_data = self.accsyn_session.get_setting(
                name='upload_location',
                integration='ftrack',
                data={'location_id': self.location_id},
            )

            if upload_location_data is None:
                # Nothing to sync
                logger.warning(
                    'Retrieved no remote location from accsyn, skipping sync.'
                )
                return

            upload_ident = self.accsyn_session.get_setting(
                name='upload_ident',
                integration='ftrack',
                data={'location_id': self.location_id},
            )
            # Locate sync job
            sync_job_name = '{} > {} ftrack sync {}'.format(
                location['name'],
                upload_location_data['name'],
                datetime.datetime.now().strftime('%y.%m.%d'),
            )

            sync_job = self.accsyn_session.find_one(
                'Job where code="{}"'.format(sync_job_name)
            )

            task_data = {
                'source': 'client={}:share={}/{}'.format(
                    self.client['id'], self.share, resource_identifier
                ),
                'destination': upload_ident,
                'metadata': {'ftrack_component_id': component['id']},
            }

            if sync_job:
                logger.info(
                    'Re-using existing sync job: "{}"'.format(sync_job_name)
                )
                logger.debug('accsyn task spec: {}'.format(task_data))
                response = self.accsyn_session.create(
                    'task', {'tasks': [task_data]}, sync_job['id']
                )
                logger.info(
                    'Successfully added 1 sync task: {}'.format(response)
                )
            else:
                logger.info(
                    'Creating new sync job: "{}"'.format(sync_job_name)
                )
                job_data = {
                    'code': sync_job_name,
                    'tasks': [task_data],
                    'mirror': True,
                    'settings': {'integration': 'ftrack'},
                    'metadata': {
                        'ftrack_workspace': self.ftrack_session.server_url,
                        'ftrack_source_location_id': location['id'],
                        'ftrack_source_location_name': location['name'],
                        'ftrack_destination_location_id': upload_location_data[
                            'id'
                        ],
                        'ftrack_destination_location_name': upload_location_data[
                            'name'
                        ],
                        'ftrack_username': self.ftrack_session.api_user,
                    },
                }
                logger.debug('accsyn job spec: {}'.format(job_data))
                response = self.accsyn_session.create('job', job_data)
                logger.info(
                    'Successfully created a new sync job: {}'.format(response)
                )
        except Exception as e:
            logger.exception(e)

    #
    # def open_(self, resource_identifier, mode="rb"):
    #     """(Override)"""
    #     if self.is_container(resource_identifier):
    #         raise AccessorResourceInvalidError(
    #             resource_identifier=resource_identifier,
    #             message="Cannot open a directory: {resource_identifier}",
    #         )
    #     return AccsynFileWrapper(
    #         super(AccsynAccessor, self).open(resource_identifier, mode=mode),
    #         self._location_id, self._share, self.get_filesystem_path(resource_identifier), self._client, self._ftrack_session, self._accsyn_session
    #     )
