// ================= MINI RAG ENGINE =================

// New line: fetch documents directly from /data folder if available
// Use this if you have a static JSON manifest or endpoint
const documents = await fetch('/data/documents.json').then(res => res.json());

// Load all data files from server endpoint (fallback / dynamic)
async function loadDataFiles() {
    let res = await fetch("/api/data/list");
    let files = await res.json();
    let docs = [];

    for (let f of files) {
        let contentRes = await fetch(`/api/data/get?filename=${encodeURIComponent(f)}`);
        let text = await contentRes.text();
        docs.push({ filename: f, text });
    }

    // Combine with static documents if any
    if (documents?.length) {
        for (let doc of documents) docs.push(doc);
    }

    return docs;
}

// ================= LAYER 2: SCORING =================
// Scores documents based on words, symbols, characters
function scoreDocument(query, docText) {
    const qWords = query.toLowerCase().split(/\W+/);
    const tWords = docText.toLowerCase().split(/\W+/);
    let wordScore = 0;

    // word-level match
    for (let w of qWords) if (tWords.includes(w)) wordScore++;

    // character-level overlap
    const chars = query.replace(/\s+/g, "").split("");
    let charScore = 0;
    for (let c of chars) if (docText.includes(c)) charScore++;

    return wordScore + 0.5 * charScore; // weighted score
}

// ================= LAYER 3: FALLBACK / PATTERN =================
function suggestClosestPattern(query, docs) {
    // find document with highest partial overlap
    let best = { text: "", score: 0 };
    for (let doc of docs) {
        let score = scoreDocument(query, doc.text);
        if (score > best.score) best = { text: doc.text, score };
    }

    if (best.score > 0) {
        return "I think you might be looking for something like this:\n\n" + best.text;
    }

    // final fallback
    return "Here’s a relevant example based on similar patterns:\n\n" + (docs[0]?.text || "");
}

// ================= MAIN QUERY FUNCTION =================
let cachedDocs = null;
async function queryMiniRAG(query) {
    if (!cachedDocs) cachedDocs = await loadDataFiles();

    // Layer 1: exact match
    for (let doc of cachedDocs) {
        if (doc.text.toLowerCase().includes(query.toLowerCase())) return doc.text;
    }

    // Layer 2: partial / relevant match
    let bestScore = -1, bestDoc = null;
    for (let doc of cachedDocs) {
        let score = scoreDocument(query, doc.text);
        if (score > bestScore) {
            bestScore = score;
            bestDoc = doc;
        }
    }
    if (bestScore > 0) return bestDoc.text;

    // Layer 3: closest pattern / suggestion
    return suggestClosestPattern(query, cachedDocs);
}
