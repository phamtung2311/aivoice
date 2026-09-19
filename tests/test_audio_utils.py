"""Exercise actual JavaScript output, including PCM layout and error cleanup."""

from pathlib import Path
import subprocess


def run_node(script):
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_wav_header_and_interleaved_clipped_samples():
    run_node("""
      const assert = require('node:assert/strict');
      require('./frontend/audio-utils.js');
      (async () => {
        const blob = AIVoiceAudio.encodeWav([
          new Float32Array([-2, 0, 2]), new Float32Array([1, 0, -1])
        ], 24000);
        const bytes = Buffer.from(await blob.arrayBuffer());
        assert.equal(blob.type, 'audio/wav');
        assert.equal(bytes.toString('ascii', 0, 4), 'RIFF');
        assert.equal(bytes.toString('ascii', 8, 12), 'WAVE');
        assert.equal(bytes.readUInt32LE(4), bytes.length - 8);
        assert.equal(bytes.readUInt16LE(22), 2);
        assert.equal(bytes.readUInt32LE(24), 24000);
        assert.equal(bytes.readUInt32LE(28), 96000);
        assert.equal(bytes.readUInt32LE(40), 12);
        assert.deepEqual([44,46,48,50,52,54].map(i => bytes.readInt16LE(i)),
          [-32768,32767,0,0,32767,-32768]);
        assert.throws(() => AIVoiceAudio.encodeWav([], 24000));
        assert.throws(() => AIVoiceAudio.encodeWav([[0], [0, 1]], 24000));
        assert.throws(() => AIVoiceAudio.encodeWav([[0]], 0));
      })().catch(error => { console.error(error); process.exitCode = 1; });
    """)


def test_playback_rejection_releases_object_url():
    app = Path("frontend/app.js").read_text()
    source = app[app.index("function playStudioBlob("):app.index("async function playAllStudioSegments(")]
    run_node(source + """
      const assert = require('node:assert/strict');
      const revoked = [];
      global.URL = {createObjectURL: () => 'blob:test', revokeObjectURL: url => revoked.push(url)};
      global.Audio = class {play() {return Promise.reject(new Error('blocked'));}};
      playStudioBlob(new Blob()).then(() => {process.exitCode = 1;}, error => {
        assert.equal(error.message, 'blocked');
        assert.deepEqual(revoked, ['blob:test']);
      });
    """)


def test_timeline_silence_uses_seconds_and_respects_pause():
    studio = Path("frontend/audio-studio.js").read_text()
    source = studio[studio.index("function playSilence("):studio.index("async function play(item)")]
    run_node(source + """
      const assert = require('node:assert/strict');
      const playback = {queueToken: 1, state: 'playing'};
      const progress = [];
      const updateTimelinePlayback = (_, elapsed) => progress.push(elapsed);
      global.performance = {now: () => 0};
      let nextFrame;
      global.requestAnimationFrame = callback => {nextFrame = callback; return 1;};
      (async () => {
        let finished = false;
        const promise = playSilence({duration_ms: 2500}, 1).then(() => {finished = true;});
        nextFrame(1000);
        await Promise.resolve();
        assert.equal(finished, false);
        assert.equal(progress.at(-1), 1);
        playback.state = 'paused';
        nextFrame(2000);
        assert.equal(progress.at(-1), 1);
        playback.state = 'playing';
        nextFrame(3500);
        await promise;
        assert.equal(progress.at(-1), 2.5);
        const cancelled = playSilence({duration_ms: 30000}, 1);
        playback.finishSilence();
        await cancelled;
        assert.equal(playback.finishSilence, null);
      })().catch(error => {console.error(error); process.exitCode = 1;});
    """)
