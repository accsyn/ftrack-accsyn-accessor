# :coding: utf-8
# :copyright: Copyright (c) 2022 accsyn/HDR AB
import os
import sys
import functools
import logging
import platform
import re
import uuid

import ftrack_api
import ftrack_api.structure.standard as _standard

logger = logging.getLogger('ftrack_accsyn_location')


def configure_location(ftrack_session, event):
    '''Setup the accsyn user staging location.'''

    logger.info('Configuring accsyn location, event: {}'.format(event))

    dependencies_directory = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'dependencies')
    )

    sys.path.append(dependencies_directory)

    import accsyn_api
    from ftrack_accsyn_accessor.accsyn import AccsynAccessor

    accsyn_session = accsyn_api.Session(dev=True)

    # Determine machine ident
    hostname = platform.node()
    mac_address = (
        ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    ).upper()

    # Load accsyn user
    user = accsyn_session.find_one(
        'User where code={}'.format(accsyn_session._username)
    )

    logger.info(
        'Got local accsyn user: {}({})'.format(user['code'], user['id'])
    )
    logger.debug('user debug: {}'.format(user))

    assert user['role'] in [
        'admin',
        'employee',
    ], 'This version of ftrack accessor does only support accsyn users having the role "admin" or "employee"!'

    # Query accsyn transfer client, based on machine and user ident
    for _client in accsyn_session.find(
        'Client where (type=0 or type=2) and user={}'.format(user['id'])
    ):
        hostname_match = _client['code'] == hostname
        mac_address_match = False
        if not hostname_match:
            # Host ID match?
            for host_id in _client['host_id'].split(','):
                if host_id.strip().upper() == mac_address:
                    mac_address_match = True
                    break
            if mac_address_match:
                client = _client
        else:
            client = _client
        if client:
            break

    assert (
        client
    ), 'Could not detect local accsyn client! Make sure you have installed and setup accsyn on local computer (hostname: {}, mac address: {})'.format(
        hostname, mac_address
    )

    logger.info(
        'Got local accsyn client: {}({})'.format(client['code'], client['id'])
    )

    # Evaluate the disk prefix from client mapped root share path
    share = accsyn_session.find_one('Share where default=true')

    logger.info(
        'Got accsyn root share: {}({})'.format(share['code'], share['id'])
    )

    # Expect environment variable set
    share_env = 'ACCSYN_{}_PATH'.format(share['code'].upper())
    assert (
        share_env in os.environ
    ), 'Root share path environment variable {} not set!'.format(share_env)

    USER_DISK_PREFIX = os.environ[share_env]

    if not os.path.exists(USER_DISK_PREFIX):
        logger.info('Creating folder {}'.format(USER_DISK_PREFIX))
        os.makedirs(USER_DISK_PREFIX)

    logger.info('Using folder: {}'.format(os.path.abspath(USER_DISK_PREFIX)))

    # Name of the location.
    USER_LOCATION_NAME = '{}.{}'.format(
        ftrack_session.api_user, platform.node()
    )

    location = ftrack_session.query(
        'Location where name="{}"'.format(USER_LOCATION_NAME)
    ).first()
    if not location:
        location = ftrack_session.ensure(
            'Location',
            {
                'name': USER_LOCATION_NAME,
                'description': 'accsyn location for user '
                ': {}, on host {}, with path: {}'.format(
                    ftrack_session.api_user,
                    platform.node(),
                    os.path.abspath(USER_DISK_PREFIX),
                ),
            },
        )

    location.accessor = AccsynAccessor(
        location['id'],
        share['code'],
        client,
        ftrack_session,
        accsyn_session,
        prefix=USER_DISK_PREFIX,
    )
    location.structure = _standard.StandardStructure()
    location.priority = 1 - sys.maxsize

    logger.warning(
        'Registering accsyn user staging location {0} @ {1} with priority {2}'.format(
            USER_LOCATION_NAME, USER_DISK_PREFIX, location.priority
        )
    )


def register(api_object, **kw):
    '''Register location with *session*.'''
    if not isinstance(api_object, ftrack_api.Session):
        return

    logger.info('Registering accsyn location')
    api_object.event_hub.subscribe(
        'topic=ftrack.api.session.configure-location',
        functools.partial(configure_location, api_object),
    )
