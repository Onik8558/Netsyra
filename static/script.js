/* ================= INITIAL VARIABLES ================= */
const editorContainer = document.getElementById("editor-container");
const preview = document.getElementById("preview");
const resizeBar = document.getElementById("resize-bar");

let isResizing = false;
let zoomLevel = 1;
let openFiles = {};
let activeFile = null;
let hotReloadTimer;
let terminals = [];
let activeTerminal = null;
let aiCollapsed = false;
let terminalExpanded = false;
let previewVisible = true;

/* ================= RESIZE ================= */
resizeBar.addEventListener("mousedown", ()=>{ 
    isResizing=true; 
    document.body.style.cursor="col-resize"; 
});

document.addEventListener("mousemove",(e)=>{
    if(!isResizing) return;
    let containerWidth = e.clientX - editorContainer.getBoundingClientRect().left;
    if(containerWidth < 200) containerWidth=200;
    if(containerWidth > window.innerWidth - 200) containerWidth=window.innerWidth - 200;
    editorContainer.style.width = containerWidth+"px";
    preview.style.width = (window.innerWidth - containerWidth - resizeBar.offsetWidth - 20)+"px";
});

document.addEventListener("mouseup",()=>{
    isResizing=false;
    document.body.style.cursor="default";
});

/* ================= ZOOM ================= */
function togglePreview(){
    const preview = document.getElementById("preview");
    const editor = document.getElementById("editor-container");

    previewVisible = !previewVisible;

    if(previewVisible){
        preview.style.display = "block";
        editor.style.width = "60%";
    }else{
        preview.style.display = "none";
        editor.style.width = "100%";
    }
}

function toggleTerminalSize(){
    const terminal = document.getElementById("terminal");
    const icon = document.getElementById("terminal-icon");

    terminalExpanded = !terminalExpanded;

    if(terminalExpanded){

        terminal.classList.add("expanded");

        // minimize icon
        icon.innerHTML = `
            <path d="M8 4h8M8 20h8"
            stroke="white" stroke-width="2" stroke-linecap="round"/>
        `;

    }else{

        terminal.classList.remove("expanded");

        // expand icon
        icon.innerHTML = `
            <path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"
            stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        `;
    }
}

function zoomIn(){
    zoomLevel+=0.1;
    document.body.style.transform=`scale(${zoomLevel})`;
    document.body.style.transformOrigin="0 0";
}
function zoomOut(){
    zoomLevel-=0.1;
    if(zoomLevel<0.6) zoomLevel=0.6;
    document.body.style.transform=`scale(${zoomLevel})`;
}

/* ================= AI TOGGLE ================= */
function toggleAIPanel(){
    const panel = document.getElementById("ai-panel");
    const arrow = document.getElementById("ai-toggle");

    aiCollapsed = !aiCollapsed;

    if(aiCollapsed){
        panel.classList.add("collapsed");
        arrow.innerText = "▶"; // indicate open
    }else{
        panel.classList.remove("collapsed");
        arrow.innerText = "◀"; // indicate close
    }
}

/* ================= REAL FREE AI  ================= */
async function askAI(){
    let prompt = `
You are coding assistant.
User question: ${document.getElementById("ai-input").value}

Current code:
${editor.getValue()}
`;

    document.getElementById("ai-output").innerText="Analyzing...";

    let res = await fetch("https://api-inference.huggingface.co/models/codellama/CodeLlama-7b-Instruct-hf",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({ inputs: prompt })
    });

    let data = await res.json();
    document.getElementById("ai-output").innerText =
        data[0]?.generated_text || "AI couldn't respond.";
}

/* ================= FILE EXPLORER ================= */

function newFile(){
    let name=prompt("File name (with extension):");
    if(!name) return;

    fetch("/api/files/save",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({filename:name,content:""})
    }).then(loadFiles);
}

function loadFiles(){
    fetch("/api/files")
    .then(r=>r.json())
    .then(files=>{
        let list=document.getElementById("file-list");
        list.innerHTML="";

        files.forEach(f=>{
            let li=document.createElement("li");
            li.style.display="flex";
            li.style.justifyContent="space-between";
            li.style.alignItems="center";

            // open file
            let nameSpan=document.createElement("span");
            nameSpan.innerText=f;
            nameSpan.onclick=()=>openFile(f);

            // rename
            let renameBtn=document.createElement("span");
            renameBtn.innerText="✏";
            renameBtn.onclick=(e)=>{
                e.stopPropagation();
                let newName=prompt("Rename:",f);
                if(!newName) return;

                fetch("/api/files/rename",{
                    method:"POST",
                    headers:{"Content-Type":"application/json"},
                    body:JSON.stringify({old:f,new:newName})
                }).then(()=>{
                    if(openFiles[f]){
                        openFiles[newName]=openFiles[f];
                        delete openFiles[f];
                    }
                    if(activeFile===f) activeFile=newName;
                    renderTabs();
                    loadFiles();
                });
            };

            // delete
            let delBtn=document.createElement("span");
            delBtn.innerText="🗑";
            delBtn.onclick=(e)=>{
                e.stopPropagation();
                if(!confirm("Delete "+f+" ?")) return;

                fetch("/api/files/delete",{
                    method:"POST",
                    headers:{"Content-Type":"application/json"},
                    body:JSON.stringify({filename:f})
                }).then(()=>{
                    delete openFiles[f];
                    if(activeFile===f){
                        activeFile=Object.keys(openFiles)[0]||null;
                        editor.setValue(activeFile?openFiles[activeFile]:"");
                    }
                    renderTabs();
                    loadFiles();
                });
            };

            li.appendChild(nameSpan);
            li.appendChild(renameBtn);
            li.appendChild(delBtn);
            list.appendChild(li);
        });
    });
}

function openFile(name){
    fetch("/api/files/open",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({filename:name})
    })
    .then(r=>r.json())
    .then(d=>{
        openFiles[name]=d.content;
        activeFile=name;
        editor.setValue(d.content);
        renderTabs();
    });
}

function saveFile(){
    if(!activeFile){
        activeFile=prompt("Save as filename:");
        if(!activeFile) return;
    }

    openFiles[activeFile]=editor.getValue();

    fetch("/api/files/save",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({filename:activeFile,content:editor.getValue()})
    });

    loadFiles();
    renderTabs();
}

loadFiles();

/* ================= TABS ================= */
function renderTabs(){
    let container=document.getElementById("file-tabs");
    container.innerHTML="";

    Object.keys(openFiles).forEach(fname=>{
        let tab=document.createElement("div");
        tab.className="tab"+(fname===activeFile?" active":"");
        tab.innerText=fname;

        let close=document.createElement("span");
        close.innerText="×";
        close.className="close-btn";
        close.onclick=(e)=>{
            e.stopPropagation();
            delete openFiles[fname];
            activeFile=Object.keys(openFiles)[0]||null;
            editor.setValue(activeFile?openFiles[activeFile]:"");
            renderTabs();
        };

        tab.appendChild(close);
        tab.onclick=()=>{ activeFile=fname; editor.setValue(openFiles[fname]); renderTabs(); };
        container.appendChild(tab);
    });
}

/* ================= RUN ENGINE ================= */
function runPython(){
    fetch("/api/run/python",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({code:editor.getValue()})
    }).then(r=>r.json()).then(d=>updateTerminalOutput(d.output));
}

function runHTML(){ document.getElementById("preview-frame").srcdoc=editor.getValue(); }
function runJS(){ document.getElementById("preview-frame").srcdoc=`<script>${editor.getValue()}<\/script>`; }

function runSmart(){
    let ext=activeFile?.split('.').pop();
    if(['html','htm'].includes(ext)) runHTML();
    else if(['js'].includes(ext)) runJS();
    else runPython();
}

/* ================= TERMINAL ================= */

function newTerminal(){
    let id=Date.now();
    terminals.push({id,output:""});
    activeTerminal=id;
    renderTerminals();
}

function renderTerminals(){
    let tabs=document.getElementById("terminal-tabs");
    let container=document.getElementById("terminal-output");

    tabs.innerHTML="";
    terminals.forEach(t=>{
        let tab=document.createElement("div");
        tab.className="terminal-tab"+(t.id===activeTerminal?" active":"");
        tab.innerText="Term "+t.id.toString().slice(-4);
        tab.onclick=()=>{activeTerminal=t.id;renderTerminals();};
        tabs.appendChild(tab);
    });

    let active=terminals.find(t=>t.id===activeTerminal);
    container.innerText=active?active.output:"";
}

function updateTerminalOutput(output){
    if(!activeTerminal) newTerminal();
    let term=terminals.find(t=>t.id===activeTerminal);
    term.output+=output+"\n";
    renderTerminals();
}

newTerminal();

/* ================= HOT RELOAD SAFE ================= */
setTimeout(()=>{
    if(window.editor){
        editor.onDidChangeModelContent(()=>{
            clearTimeout(hotReloadTimer);
            hotReloadTimer=setTimeout(()=>{
                if(activeFile?.endsWith(".html")) runHTML();
                else if(activeFile?.endsWith(".js")) runJS();
            },500);
        });
    }
},1000);

/* ================= SHORTCUTS ================= */
document.addEventListener("keydown", e=>{
    if(e.ctrlKey && e.key==="s"){ e.preventDefault(); saveFile(); }
    if(e.ctrlKey && e.key==="r"){ e.preventDefault(); runSmart(); }
});
