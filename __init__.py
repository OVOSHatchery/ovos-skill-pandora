from os.path import join, dirname

from ovos_plugin_common_play.ocp import MediaType, PlaybackType
from ovos_utils.parse import fuzzy_match
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill, \
    ocp_search
from pandorinha import Pandora


class PandoraSkill(OVOSCommonPlaybackSkill):
    def __init__(self):
        super(PandoraSkill, self).__init__("Pandora")
        self.supported_media = [MediaType.GENERIC,
                                MediaType.MUSIC]
        self.skill_icon = join(dirname(__file__), "ui", "pandora.jpeg")
        self.pandora = Pandora()

    def initialize(self):
        self.pandora.login()

    # score
    @staticmethod
    def calc_score(phrase, match, base_score=0, exact=False):

        if exact:
            # this requires that the result is related
            if phrase.lower() in match["title"].lower():
                match["match_confidence"] = max(match["match_confidence"], 80)
            elif phrase.lower() in match["artist"].lower():
                match["match_confidence"] = max(match["match_confidence"], 85)
            elif phrase.lower() == match["station"].lower():
                match["match_confidence"] = max(match["match_confidence"], 70)
            else:
                return 0

        score = max(base_score, match["match_confidence"] / 2)

        title_score = 100 * fuzzy_match(phrase.lower(),
                                        match["title"].lower())
        artist_score = 100 * fuzzy_match(phrase.lower(),
                                         match["artist"].lower())
        if artist_score > 85:
            score += artist_score * 0.85 + title_score * 0.15
        elif artist_score > 70:
            score += artist_score * 0.6 + title_score * 0.4
        elif artist_score > 50:
            score += title_score * 0.5 + artist_score * 0.5
        else:
            score += title_score * 0.8 + artist_score * 0.2
        score = min((100, score))
        return score

    @ocp_search()
    def search_pandora(self, phrase, media_type=MediaType.GENERIC):
        max_results = 30
        # match the request media_type
        base_score = 0
        if media_type == MediaType.MUSIC:
            base_score += 10
        else:
            base_score -= 15  # big penalty because pandora returns similar
            # artists, we most likely don't want to select this, pandora is
            # better suited for playlist/station search which will be done in
            # a different handler

        explicit_request = False
        if self.voc_match(phrase, "pandora"):
            # explicitly requested pandora
            base_score += 50
            phrase = self.remove_voc(phrase, "pandora")
            explicit_request = True
            self.extend_timeout(1)

        n = 0
        for r in self.pandora.similar(phrase):
            yield {
                "match_confidence": self.calc_score(phrase, r, base_score,
                                                    exact=not explicit_request),
                "media_type": MediaType.MUSIC,
                "length": r["duration"] * 1000,  # seconds to milliseconds
                "uri": r["uri"],
                "playback": PlaybackType.AUDIO,
                "image": r["image"],
                "bg_image": r["bg_image"],
                "skill_icon": self.skill_icon,
                "skill_logo": self.skill_icon,  # backwards compat
                "title": r["title"],
                "artist": r["artist"],
                "album": r["album"],
                "skill_id": self.skill_id
            }
            if n > max_results:
                break
            n += 1


def create_skill():
    return PandoraSkill()
