/* ================= MONACO EDITOR SETUP ================= */
require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.39.0/min/vs' } });

require(['vs/editor/editor.main'], function () {

    // Create Monaco Editor in the container
    window.editor = monaco.editor.create(document.getElementById('editor-container'), {
        value: '# Start coding\nprint("Hello IDE")',
        language: 'python',
        theme: 'vs-dark',
        automaticLayout: true,
        minimap: { enabled: true },
        fontSize: 14,
        fontFamily: 'Consolas, monospace'
    });

    // Set up hot reload preview for HTML/JS (optional if using script.js)
    window.editor.onDidChangeModelContent(()=>{
        if(typeof hotReloadTimer!=='undefined'){
            clearTimeout(hotReloadTimer);
            hotReloadTimer = setTimeout(()=>{
                let code = editor.getValue();
                if(activeFile && (activeFile.endsWith(".html") || code.includes("<html"))) runHTML();
                else if(activeFile && (activeFile.endsWith(".js") || code.includes("document.") || code.includes("window."))) runJS();
            },500);
        }
    });
});

/* ================= SUPPORTED LANGUAGES ================= */
window.languages = ['python','javascript','html','css','java','c','cpp'];

/* ================= LANGUAGE SELECTOR ================= */
function setLanguage(lang){
    if(!window.languages.includes(lang)) return;
    monaco.editor.setModelLanguage(editor.getModel(), lang);
}
