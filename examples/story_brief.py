"""Build and display a privacy-safe Arc Story Brief v1 understanding."""

from pprint import pprint

from narraiva_arc.brief import BriefValues, interpret_story_brief


def main() -> None:
    brief = interpret_story_brief(
        "A lighthouse keeper hears tomorrow's distress calls.",
        inferred=BriefValues(genre="speculative fiction", setting="an isolated lighthouse"),
        explicit=BriefValues(tone="tense", must_avoid=("graphic violence",)),
    )
    pprint(brief.to_user_view(), sort_dicts=False)


if __name__ == "__main__":
    main()
