# ftrack-accsyn-accessor

A ftrack API location accessor enabling background file transfers with accsyn file synchronisation tool.

About
-----

The accessor registers with the ftrack Python API and creates a local staging area location for data, 
where files first are copied before synchronized with accsyn.

accsyn is a file and workflow metadata synchronisation tool leveraging a RSYNC-like p2p protocol with
100% encrypted data transfer and acceleration. For more information: https://accsyn.com

ftrack is the widely acknowledged web based media project management and review tool for the creative industry. 
For more information: https://ftrack.com

The accessor enables the following feature set:

* Eliminates the need for a separate file transfer tool such as FTP, Dropbox, WeTransfer, etc.
* Makes sure all published files are transfered securely by fastest means possible to the on-premise/cloud storage.
* Allows for a single point of access to all published files, regardless of where they are stored.
* Integrates with ftrack's existing Storage scenario or other storage/location solutions.
* Leverages the existing ftrack Location system, for more information: https://www.ftrack.com/en/intro-to-locations-webinar
* 


Prerequisites
-------------

This plugin is intended to run on a machine having accsyn app installed and configured,
this includes setting these user/system environment variables:

```bash
ACCSYN_API_KEY=secret API key

ACCSYN_API_USER=my.mail@org.com

ACCSYN_DOMAIN=the accsyn workspace (e.g. the domain in domain.accsyn.com)

ACCSYN_PROJECTS_PATH=<local staging area path to root share/main storage named "projects">
```


The accessor requires an active accsyn v2.3 or later subscription with the ftrack integration configured in active.

The accessor is designed to be installed and run with ftrack Connect.


# Installation

Download the prebuilt plugin from the [releases](https://github.com/accsyn/ftrack-accsyn-accessor/releases) and drop it onto the ftrack Connect plugin manager.

## Building

To build the plugin from source, clone the repository and run the following commands:

    $ python setup.py build_plugin

**_NOTE:_**  Connect is compatible with plugins built with Python 3.7-3.9.

## Usage

### Connect and the DCC integrations Framework

The accsyn accessor will be automatically registered with the ftrack Python API leveraged 
by Connect and the DCC integrations Framework when launched from Connect.

### ftrack API standalone

To use the accessor with a standalone API session, first ensure to have the accsyn accessor built and then set the following environment variables:

```bash
FTRACK_EVENT_PLUGIN_PATH=<path to build folder>/ftrack-accsyn-accessor-0.3.1/hook
```

Then launch the API session:

```python
    import ftrack_api
    session = ftrack_api.Session(auto_connect_event_hub=True)

    # Proceed using the session as usual, publish creating components
```

# Release Notes

## [0.3.1] - 2022-12-08

### New

* Initial release


# License

This project is licensed under the terms of the Apache 2.0 license.

# Support

For support, please first pay a visit to https://support.accsyn.com. If that does not answer your questions,  drop an email to: support@accsyn.com 

