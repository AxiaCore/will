#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
import json
import random
import requests

from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, hear, randomly, require_settings

from pyquery import PyQuery as pq


class AxiaCorePlugin(WillPlugin):

    @hear('commit')
    def talk_on_commit(self, message):
        doc = pq(url='http://whatthecommit.com/')
        text = doc('#content p:first').text()
        self.say(
            '@{0} try this commit message: {1}'.format(
                message.sender.nick,
                text,
            ),
            message=message,
        )

    @hear('pug')
    def talk_on_pug(self, message):
        req = requests.get('http://pugme.herokuapp.com/random')
        if req.ok:
            self.say(req.json()['pug'], message=message)

    @hear('deploy')
    def talk_on_deploy(self, message):
        doc = pq(url='http://devopsreactions.tumblr.com/random')
        self.say(doc('.post_title').text(), message=message)
        self.say(doc('.item img').attr('src'), message=message)

    @require_settings('DOOR_URL')
    @respond_to('^op$|^open the door$')
    def open_the_door(self, message):
        req = requests.get(settings.DOOR_URL)
        if req.ok:
            self.reply(
                message, 'Say welcome %s!' % message.sender.nick.title()
            )
        else:
            self.reply(message, 'I could not open the door', color='red')

    @require_settings('AUDIO_URL')
    @respond_to('^stop$')
    def stop_the_beat(self, message):
        data = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': '',
        }

        # Stop current playback
        data['method'] = 'core.playback.stop'
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )
        if not req.ok:
            self.reply(message, 'I could not stop the playback', color='red')
            return

        # Clear tracklist
        data['method'] = 'core.tracklist.clear'
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )
        if not req.ok:
            self.reply(message, 'I could not clear the tracklist', color='red')
            return

        self.reply(message, 'Silence please!')

    @require_settings('AUDIO_URL')
    @respond_to('^play$|^play (?P<url>.*)$')
    def play_the_beat(self, message, url=None):
        data = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': '',
        }

        # Stop current playback
        data['method'] = 'core.playback.stop'
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )
        if not req.ok:
            self.reply(message, 'I could not stop the playback', color='red')
            return

        # Clear tracklist
        data['method'] = 'core.tracklist.clear'
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )
        if not req.ok:
            self.reply(message, 'I could not clear the tracklist', color='red')
            return

        # Get a stream to play
        if url is None:
            # Play some radio
            radio_list = [
                'http://www.977music.com/itunes/90s.pls',
                'http://www.977music.com/itunes/mix.pls',
                'http://www.977music.com/itunes/jazz.pls',
                'http://www.977music.com/977hicountry.pls',
                'http://www.977music.com/itunes/alternative.pls',
                'http://www.977music.com/itunes/oldies.pls',
                'http://www.977music.com/itunes/80s.pls',
                'http://www.977music.com/itunes/classicrock.pls',
                'http://www.977music.com/itunes/hitz.pls',
                'http://nprdmp.ic.llnwd.net/stream/nprdmp_live01_mp3',
                'http://icecast.omroep.nl/3fm-bb-mp3',
                'http://vprbbc.streamguys.net:8000/vprbbc24.mp3',
                'http://somafm.com/groovesalad.pls',
                'http://stream.kissfm.de/kissfm/mp3-128/internetradio/',
                'http://pr320.pinguinradio.com/listen.pls',
            ]
            url = random.choice(radio_list)

        # Add prefix for mopidy backends
        if 'youtube.com' in url:
            url = 'yt:%s' % url
        elif 'grooveshark.com' in url:
            url = 'gs:%s' % url

        # Add new stream
        data['method'] = 'core.tracklist.add'
        data['params'] = {
            'tracks': None,
            'at_position': None,
            'uri': None,
            'uris': [url],
        }
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )

        if not req.ok:
            self.reply(message, 'I could not add the stream', color='red')
            return

        track_name = req.json()['result'][0]['track'].get('name', url)

        # Play the beat
        del data['params']
        data['method'] = 'core.playback.play'
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )

        if req.ok:
            self.reply(
                message, '"%s" will be playing for you %s' % (
                    track_name, message.sender.nick.title()
                )
            )
        else:
            self.reply(message, 'I could not play the stream', color='red')

    @randomly(
        start_hour='9',
        end_hour='16',
        day_of_week="mon-fri",
        num_times_per_day=2,
    )
    def hold_my_beer(self):
        req = requests.get(
            'http://www.reddit.com/r/holdmybeer/top/.json?sort=top&t=week',
            headers={'User-Agent': 'Mozilla/5.0'},
        )
        if req.ok:
            elem = random.choice(req.json()['data']['children'])
            url = elem['data']['url']
            if url.endswith('.gifv'):
                url = url.replace('.gifv', '.gif')

            self.say(url)
            self.say(elem['data']['title'])
        else:
            self.say(req.reason, color='red')
