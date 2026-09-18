// ---------------------------------------------------------------------------
// Voix ElevenLabs — Text-to-Speech (la voix qui explique la page).
// Proxy serveur : la clé ELEVENLABS_API_KEY ne quitte JAMAIS le back.
// Le front envoie le texte déjà rédigé dans la langue choisie ; on renvoie
// l'audio (mp3). Modèle multilingue → FR/EN/DE/ES/IT.
// ---------------------------------------------------------------------------


// Voix multilingue par défaut (« Rachel ») — surchargée par ELEVENLABS_VOICE_ID.
const DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM";

export async function POST(req: Request): Promise<Response> {
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) {
    return Response.json({ error: "no_elevenlabs_key" }, { status: 503 });
  }

  let text = "";
  try {
    const body = (await req.json()) as { text?: string };
    text = (body.text ?? "").toString().slice(0, 2500); // garde-fou coût/latence
  } catch {
    /* body vide */
  }
  if (!text.trim()) {
    return Response.json({ error: "empty_text" }, { status: 400 });
  }

  const voice = process.env.ELEVENLABS_VOICE_ID || DEFAULT_VOICE;

  try {
    const el = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}`, {
      method: "POST",
      headers: {
        "xi-api-key": key,
        "Content-Type": "application/json",
        Accept: "audio/mpeg",
      },
      body: JSON.stringify({
        text,
        model_id: "eleven_multilingual_v2",
        voice_settings: { stability: 0.5, similarity_boost: 0.75 },
      }),
    });

    if (!el.ok) {
      const detail = await el.text().catch(() => "");
      console.error("ElevenLabs TTS échoué :", el.status, detail.slice(0, 300));
      return Response.json({ error: `elevenlabs_${el.status}` }, { status: 502 });
    }

    const audio = await el.arrayBuffer();
    return new Response(audio, {
      headers: { "Content-Type": "audio/mpeg", "Cache-Control": "no-store" },
    });
  } catch (err) {
    console.error("Voix (réseau) échouée :", err);
    return Response.json({ error: "network" }, { status: 502 });
  }
}
