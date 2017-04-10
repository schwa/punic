from __future__ import division, absolute_import, print_function

__all__ = ['Platform', 'parse_platforms']

from .errors import *

class Platform(object):
    all = []

    def __init__(self, name, nickname, sdks, output_directory_name):
        self.name = name
        # TODO: Change to "display name"?
        self.nickname = nickname
        self.sdks = sdks
        self.output_directory_name = output_directory_name

    @classmethod
    def platform_for_nickname(cls, nickname):
        # type: (str) -> Platform
        for platform in cls.all:
            if platform.nickname.lower() == nickname.lower():
                return platform
        return None

    @property
    def device_sdk(self):
        return self.sdks[0]

    def __repr__(self):
        return self.nickname


Platform.all = [
    Platform(name='iOS', nickname='iOS', sdks=['iphoneos', 'iphonesimulator'], output_directory_name='iOS'),
    Platform(name='macOS', nickname='Mac', sdks=['macosx'], output_directory_name='Mac'), # TODO: Change path to macOS? Will SDK name change?
    Platform(name='watchOS', nickname='watchOS', sdks=['watchos', 'watchsimulator'], output_directory_name='watchOS'),
    Platform(name='tvOS', nickname='tvOS', sdks=['appletvos', 'appletvsimulator'], output_directory_name='tvOS')
]


def parse_platforms(platforms):
    # type: (str) -> [Platform]

    if not platforms:
        return Platform.all
    else:
        platforms = [platform.strip() for platform in platforms.split(',')]
        platforms = [Platform.platform_for_nickname(platform) for platform in platforms]
        return platforms
    raise PunicException('Cannot parse platforms')

