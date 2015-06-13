# -*- coding: utf-8 -*-
# Copyright 2015 Zalinasco (zalinasco@outlook.com)
#
# This file is part of subliminal.
#
# subliminal is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# subliminal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with subliminal.  If not, see <http://www.gnu.org/licenses/>.
from . import ServiceBase
from ..cache import cachedmethod
from ..exceptions import DownloadFailedError
from ..language import Language, language_set
from ..subtitles import get_subtitle_path, ResultSubtitle
from ..utils import get_keywords, split_keyword
from ..videos import Episode
from sickbeard import logger
from bs4 import BeautifulSoup
import zipfile
import StringIO
import logging
import os
import re
import sys

class Subspedia(ServiceBase):
    server_url = 'http://www.subspedia.tv'
    site_url = 'http://www.subspedia.tv'
    api_based = False
    languages = language_set(['it'])
    language_map = {'Italian': Language('it')}
    videos = [Episode]
    require_video = False
    required_features = ['permissive']
    
    @cachedmethod
    def get_series_id(self, name):
        """Get the show page and cache every show found in it"""
        r = self.session.get('%s/listaSerieTestuale.php' % self.server_url)
        soup = BeautifulSoup(r.content, self.required_features)
        for html_series in soup.select('td[class=titoloSerie] > a'):
            series_name = html_series.text.lower()
            match = re.search('serie.php\\?id=([0-9]+)', html_series['href'])

            logger.log(u'Subspedia connector: get_series_id found %s' % (series_name), logger.INFO)

            if match is None:
                continue
            series_id = int(match.group(1))
            self.cache_for(self.get_series_id, args=(series_name,), result=series_id)
        return self.cached_value(self.get_series_id, args=(name,))

    def list_checked(self, video, languages):
        return self.query(video.path or video.release, languages, get_keywords(video.guess), video.series, video.season, video.episode)

    def query(self, filepath, languages, keywords, series, season, episode):

        logger.log(u'Subspedia connector: searching for subtitles for %s season %d episode %d with languages %r' % (series, season, episode, languages), logger.INFO)

        self.init_cache()
        try:
            series_id = self.get_series_id(series.lower())
        except KeyError:
            logger.log(u'Could not find series id for %s' % (series), logger.ERROR)
            return []
        r = self.session.get('%s/serie.php?id=%d' % (self.server_url, series_id))
        soup = BeautifulSoup(r.content, self.required_features)
        subtitles = []

        linkmarker = "-S%d-E%d-%d-" % (season, episode, series_id)
        logger.log(u'Subspedia connector: linkmarker is %s' % (linkmarker), logger.INFO)
    
        links = soup.find_all(href=re.compile("downloadSub[^\-]*" + linkmarker))
        
        logger.log(u'Subspedia connector: found %d links ' % (len(links)), logger.INFO)

        for link in links:

            linkhref = link['href']
            logger.log(u'Subspedia connector: examining link: %s' % (linkhref), logger.INFO)
            
            if linkmarker in linkhref:
                
                linkhref = linkhref[24:]
                linkhref = linkhref[:linkhref.find('"')]
                logger.log(u'Subspedia connector: !!found!! link: %s' % (linkhref), logger.INFO)
                sub_language = self.get_language('Italian')
                sub_link = '%s/%s' % (self.server_url, linkhref)
                sub_path = get_subtitle_path(filepath, sub_language, self.config.multi)
                subtitle = ResultSubtitle(sub_path, sub_language, self.__class__.__name__.lower(), sub_link)
                logger.log(u'Subspedia connector: returning %s' % (subtitle), logger.INFO)
                subtitles.append(subtitle)

        return subtitles

    def download(self, subtitle):
        logger.log(u'Downloading %s in %s' % (subtitle.link, subtitle.path), logger.INFO)
        try:
            r = self.session.get(subtitle.link, headers={'Referer': subtitle.link, 'User-Agent': self.user_agent})

            subfile = r.content
            
            if ".zip" in subtitle.link:
                zipcontent = StringIO.StringIO(r.content)
                zipsub = zipfile.ZipFile(zipcontent)
                subfile = zipsub.open(zipsub.namelist()[0]).read()
                zipsub.close()

            with open(subtitle.path, 'wb') as f:
                f.write(subfile)
            
        except Exception as e:
            logger.log(u'Download failed: %s' % e, logger.ERROR)
            if os.path.exists(subtitle.path):
                os.remove(subtitle.path)
            raise DownloadFailedError(str(e))
        logger.log(u'Download finished', logger.INFO)
        return subtitle


Service = Subspedia
