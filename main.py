import json
import random
import time

from flask import Flask, render_template, url_for, make_response, request, redirect
from game import Game, SEC_STEPS
from song import Skip, Guess, Blank


game = Game()


def complete_share_text(share_text: str | None = None) -> str:
    if share_text is None:
        share_text = request.cookies["share_text"]
    share_text += "⬜" * (6 - len(share_text))
    share_text = f"#Listendle #{game.game_num}\\n\\n🔊" + share_text + "\\n\\nhttps://listendle.herokuapp.com"

    return share_text


app = Flask(__name__)
HISTORY_DEFAULT = []
for _ in range(6):
    entry = Blank().__dict__
    entry["type"] = "Blank"
    HISTORY_DEFAULT.append(entry)

WON_RESULT_WORDS = ["Congrats!", "Well done!", "Incredible!", "Amazing!"]
LOST_RESULT_WORDS = ["Unlucky!", "Better luck next time!", "Awww!", "Close!"]


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    game.update()

    if request.cookies.get("secs") is None or request.cookies.get("date") is None or request.cookies["date"] != game.today_song.date:
        resp = make_response(render_template(
            "index.html",
            songs=[str(song) for song in game.all_songs],
            secs=1,
            secs_display="01",
            history=json.dumps(HISTORY_DEFAULT),
            show_blank=True,
        ))
        resp.set_cookie("secs", "1")
        resp.set_cookie("date", game.today_song.date)
        resp.set_cookie("result", "none")
        resp.set_cookie("skip_redirect", "false")
        resp.set_cookie("share_text", "")
        resp.set_cookie("history", json.dumps(HISTORY_DEFAULT))

        return resp

    if request.cookies.get("result") not in [None, "none"]:
        return redirect(url_for("result"))

    if request.cookies["secs"] == "30":
        resp = make_response(redirect(url_for("result")))
        resp.set_cookie("result", "lost")
        resp.set_cookie("share_text", complete_share_text())
        resp.set_cookie("song_name", game.today_song.name)
        resp.set_cookie("song_artist", game.today_song.artist)

        return resp

    if request.method == "POST":
        if request.form["guess"] == str(game.today_song):
            resp = make_response(redirect(url_for("result")))
            resp.set_cookie("result", "won")

            share_text = request.cookies["share_text"]
            share_text += "🟩"
            resp.set_cookie("share_text", complete_share_text(share_text))

            resp.set_cookie("song_name", game.today_song.name)
            resp.set_cookie("song_artist", game.today_song.artist)

            return resp
        resp = make_response(redirect(url_for("skip")))

        share_text = request.cookies["share_text"]
        share_text += "🟥"
        resp.set_cookie("share_text", share_text)
        resp.set_cookie("skip_redirect", "true")

        history = json.loads(request.cookies["history"])
        entry = Guess(*request.form["guess"].split(" – ")).__dict__
        entry["type"] = "Guess"
        history[SEC_STEPS.index(int(request.cookies["secs"]))] = entry
        resp.set_cookie("history", json.dumps(history))

        return resp

    return render_template(
        "index.html",
        songs=[str(song) for song in game.all_songs],
        secs=int(request.cookies["secs"]),
        secs_display=request.cookies["secs"].zfill(2),
        history=json.loads(request.cookies["history"]),
        show_blank=False,
    )

@app.route("/skip", methods=["GET", "POST"])
def skip() -> str:
    if request.cookies.get("secs") is None:
        return redirect("/")

    secs = int(request.cookies["secs"])
    secs = SEC_STEPS[SEC_STEPS.index(secs) + 1]
    resp = make_response(redirect("/"))

    if request.cookies["skip_redirect"] == "false":
        share_text = request.cookies["share_text"]
        share_text += "⬛"
        resp.set_cookie("share_text", share_text)

        history = json.loads(request.cookies["history"])
        entry = Skip().__dict__
        entry["type"] = "Skip"
        history[SEC_STEPS.index(int(request.cookies["secs"]))] = entry
        resp.set_cookie("history", json.dumps(history))
    else:
        resp.set_cookie("skip_redirect", "false")

    resp.set_cookie("secs", str(secs))

    return resp

@app.route("/result")
def result() -> str:
    if request.cookies.get("result") not in ["won", "lost"]:
        return redirect("/")

    if request.cookies["result"] == "won":
        secs = request.cookies['secs']
        word = "second" if secs == "1" else "seconds"
        result_word = random.choice(WON_RESULT_WORDS)
        result_text = f"You guessed the song in {secs} {word}."
    else:
        result_word = random.choice(LOST_RESULT_WORDS)
        result_text = "You didn't guess the song correctly."

    score_text = " ".join(list(request.cookies["share_text"].split("\\n\\n")[1][1:]))
    return render_template(
        "result.html",
        secs=request.cookies["secs"],
        song_name=request.cookies["song_name"],
        song_artist=request.cookies["song_artist"],
        result_word=result_word,
        result_text=result_text,
        score_text=score_text,
        share_text=request.cookies["share_text"],
    )


if __name__ == "__main__":
    app.run()
