function toggleModal(id){document.getElementById(id).classList.toggle("show")}
function addMember(){const c=document.getElementById("members");const r=document.createElement("div");r.className="member-row";r.innerHTML='<input name="member_name" placeholder="Name"><input name="member_email" placeholder="Email"><input name="member_role" placeholder="Role"><input name="member_resp" placeholder="Responsibilities">';c.appendChild(r)}
document.addEventListener("click",async e=>{
 const b=e.target.closest(".task-check");
 if(b){const id=b.dataset.task,status=b.dataset.status;const r=await fetch("/task/"+id+"/status",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({status})});if(r.ok)location.reload();}
});
document.querySelectorAll(".status-select").forEach(s=>s.addEventListener("change",async()=>{await fetch("/task/"+s.dataset.task+"/status",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({status:s.value})});}));
document.querySelectorAll(".contact-status").forEach(s=>s.addEventListener("change",async()=>{await fetch("/contact/"+s.dataset.contact+"/status",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({status:s.value})});}));
async function askAssistant(eventId){const input=document.getElementById("assistantInput"),box=document.getElementById("assistantAnswer");if(!input.value.trim())return;box.style.display="block";box.textContent="Thinking…";const r=await fetch("/event/"+eventId+"/assistant",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:input.value})});const d=await r.json();box.textContent=d.answer;}
setTimeout(()=>document.querySelectorAll(".toast").forEach(x=>x.remove()),4500);
