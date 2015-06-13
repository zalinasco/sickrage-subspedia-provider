# sickrage-subspedia-provider
A subtitles provider fo SickRage that works with the excellent Subspedia.tv blog.

To make it work you will have to modify your sickrage/lib/subliminal/core.py, adding the provider to the SERVICES list.

Your core.py should change from:

SERVICES = ['opensubtitles', 'subswiki', 'subtitulos', 'thesubdb', 'addic7ed', 'tvsubtitles', 'itasa',
            'usub', 'subscenter']

to:
            
SERVICES = ['opensubtitles', 'subswiki', 'subtitulos', 'thesubdb', 'addic7ed', 'tvsubtitles', 'itasa',
            'usub', 'subscenter','subspedia']

or something like that.

Then copy the subspedia.py file in your sickrage/lib/subliminal/services, restart SickRage and enable the provider in the "Subtitles Settings" page of SickRage.