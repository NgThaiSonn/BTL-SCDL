"use strict";
const $ = selector => document.querySelector(selector);
const routes = {home:"Tổng quan",customers:"Khách hàng",accounts:"Tài khoản",transactions:"Giao dịch",reports:"Báo cáo",employees:"Nhân viên"};
const glyphs = {home:"M3 4h7v7H3z M14 4h7v7h-7z M3 15h7v6H3z M14 15h7v6h-7z",
  customers:"M15 20v-2a5 5 0 0 0-10 0v2 M10 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M17 6a3 3 0 0 1 0 6 M18 15a4 4 0 0 1 3 4",
  accounts:"M3 6h18v13H3z M3 10h18 M6 15h4",
  transactions:"M3 7h16l-4-4 M21 17H5l4 4",reports:"M4 3v18h17 M8 17v-5 M13 17V7 M18 17v-8",employees:"M3 7h18v13H3z M8 7V4h8v3 M3 12q9 5 18 0"};
const labels = {NAP:"Nộp tiền",CHI:"Chi tiêu",TRA:"Trả dư nợ",GUI:"Gửi tiền",TD:"Tín dụng",KINH_DOANH:"Kinh doanh",GIAO_DICH:"Giao dịch viên",QUAN_LY:"Quản lý"};
const esc = value => String(value ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
const money = value => {
  const [whole,fraction] = String(value ?? "0").split(".");
  return BigInt(whole).toLocaleString("vi-VN") + (fraction && Number(fraction) ? ","+fraction.replace(/0+$/,"") : "");
};
const fmtDay = value => value ? value.slice(0,10).split("-").reverse().join("/") : "—";
const fmtTime = value => value ? fmtDay(value)+" "+value.slice(11,16) : "—";
const tag = value => `<span class="pill ${esc(value)}">${esc(labels[value] || value)}</span>`;
const navIcon = key => `<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="${glyphs[key]}"/></svg>`;
const page = $("#page"), dialog = $("#dialog");
let state={}, route="home", report="salary", txnKind="TRA", seq=0, reportSeq=0;
let period={}, reportCache=null;
$("#nav").innerHTML=Object.entries(routes).map(([k,v])=>`<a href="#${k}" data-nav="${k}">${navIcon(k)}${v}</a>`).join("");
$("#close-dialog").onclick=()=>dialog.close();
dialog.addEventListener("click",e=>{if(e.target===dialog && (e.clientX<dialog.getBoundingClientRect().left || e.clientX>dialog.getBoundingClientRect().right || e.clientY<dialog.getBoundingClientRect().top || e.clientY>dialog.getBoundingClientRect().bottom))dialog.close();});
async function api(path, method="GET", body){
  const resp=await fetch("/api/"+path,{method,headers:body?{"Content-Type":"application/json"}:{},body:body?JSON.stringify(body):undefined});
  const data=await resp.json();
  if(!resp.ok) throw new Error(data.error || "Yêu cầu chưa hoàn tất.");
  return data;
}
function notify(message,bad=false){$("#notice").innerHTML=message?`<div class="${bad?"error":"success"}">${esc(message)}</div>`:"";}
function header(title,sub="",action=""){return `<div class="heading"><div><h1>${title}</h1>${sub?`<p>${sub}</p>`:""}</div>${action}</div>`;}
function button(id,label,kind="primary"){return `<button type="button" class="${kind}" id="${id}">${label}</button>`;}
function table(rows,cols){
  if(!rows.length)return '<p class="empty">Không có dữ liệu phù hợp.</p>';
  return `<div class="tablewrap"><table><thead><tr>${cols.map(c=>`<th class="${c[2]==="money"?"num":""}">${c[1]}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${cols.map(([key,title,type])=>{
    const v=r[key]; let display=esc(v??"—");
    if(type==="money")display=money(v);
    if(type==="date")display=fmtDay(v);
    if(type==="time")display=fmtTime(v);
    if(type==="tag")display=tag(v);
    if(typeof type==="function")display=type(r);
    return `<td class="${type==="money"?"num":type==="code"?"code":""}">${display}</td>`;
  }).join("")}</tr>`).join("")}</tbody></table></div>`;
}
function options(rows,key,label){return rows.map(r=>`<option value="${esc(r[key])}">${esc(label(r))}</option>`).join("");}
function select(name,title,opts,wide=false){return `<label class="${wide?"wide":""}">${title}<select name="${name}" required>${opts}</select></label>`;}
function input(name,title,type="text",attrs=""){return `<label>${title}<input name="${name}" type="${type}" required ${attrs}></label>`;}
function form(inner,submit){return `<form><div class="fieldgrid">${inner}</div><div class="form-error" role="alert"></div><button class="primary" type="submit">${submit}</button></form>`;}
function modal(title,html){$("#dialog-title").textContent=title;$("#dialog-body").innerHTML=html;dialog.showModal();}
function bindForm(el,handler){
  el.onsubmit=async e=>{
    e.preventDefault();const btn=el.querySelector("[type=submit]"), error=el.querySelector(".form-error");
    btn.disabled=true;error.textContent="";
    try{await handler(Object.fromEntries(new FormData(el)));}
    catch(err){error.innerHTML=`<p class="error">${esc(err.message)}</p>`;}
    finally{btn.disabled=false;}
  };
}
async function refresh(message){
  if(dialog.open)dialog.close();
  await navigate();notify(message);
}
function setRoute(r){location.hash=r;}
function home(){
  const t=state.overview.totals,top=state.top.slice(0,4);
  const metrics=[["Tổng tiền gửi",money(t.tong_gui),"₫"],["Dư nợ tín dụng",money(t.du_no),"₫"],["Khách hàng",t.khach,""],["Tài khoản",t.tai_khoan,""]];
  page.innerHTML=header("Tổng quan chi nhánh","",button("do-pay","Thanh toán dư nợ"))+`<div class="metrics">${metrics.map(m=>`<article class="metric"><span class="title">${m[0]}</span><strong>${m[1]}<small>${m[2]}</small></strong></article>`).join("")}</div>
    <div class="home-grid"><article class="panel"><div class="sectionhead"><h2>Giao dịch gần đây</h2></div>${table(state.overview.recent,[["luc","Thời điểm","time"],["loai","Nghiệp vụ","tag"],["ho_ten","Người thực hiện"],["so_tien","Số tiền (₫)","money"]])}</article>
    <article class="panel"><div class="sectionhead"><h2>Tiền gửi cao nhất</h2>${button("all-top","Xem 10","linkbutton")}</div>${top.map(r=>`<div class="rank"><div><strong>${esc(r.ho_ten)}</strong><em>${money(r.tong_gui)} ₫</em></div><span class="bar"><i style="width:${Number(top[0].tong_gui)>0?100*Number(r.tong_gui)/Number(top[0].tong_gui):0}%"></i></span></div>`).join("") || '<p class="empty">Chưa có tiền gửi.</p>'}</article></div>`;
  $("#do-pay").onclick=()=>{txnKind="TRA";setRoute("transactions");};
  $("#all-top").onclick=()=>{report="top";setRoute("reports");};
}
const normalize=s=>String(s).toLocaleLowerCase("vi").normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/đ/g,"d");
function searchable(rows,cols,keys){
  const list=$("#directory"),box=$("#searchbox");
  function draw(){const query=normalize(box.value.trim());list.innerHTML=table(rows.filter(r=>keys.some(k=>normalize(r[k]).includes(query))),cols);}
  box.oninput=draw;draw();
}
const searchbar=(label)=>`<div class="filters"><label class="search">${label}<input id="searchbox" type="search" placeholder="Nhập từ khóa…"></label></div><div id="directory"></div>`;
function customers(){
  page.innerHTML=header("Khách hàng","",button("new-customer","Thêm khách hàng"))+`<div class="panel">${searchbar("Tìm theo mã, tên hoặc CMT")}</div>`;
  searchable(state.customers,[["ma_kh","Mã KH","code"],["ho_ten","Họ và tên"],["cmt","CMT / CCCD"],["ngay_sinh","Ngày sinh","date"],["dia_chi","Địa chỉ"],["","",r=>`<button class="linkbutton" data-address="${esc(r.ma_kh)}">Sửa địa chỉ</button>`]],["ma_kh","ho_ten","cmt"]);
  $("#new-customer").onclick=()=>{
    modal("Thêm khách hàng",form(input("ma_kh","Mã khách hàng","text",'maxlength="12" pattern="[A-Za-z0-9_\\-]+"')+input("ho_ten","Họ và tên","text",'maxlength="100"')+input("cmt","Số CMT / CCCD","text",'pattern="([0-9]{9}|[0-9]{12})" maxlength="12"')+input("ngay_sinh","Ngày sinh","date")+input("dia_chi","Địa chỉ","text",'maxlength="200"'),"Lưu khách hàng"));
    bindForm($("#dialog form"),async d=>refresh((await api("customers","POST",d)).message));
  };
  $("#directory").onclick=e=>{const b=e.target.closest("[data-address]");if(!b)return;
    const r=state.customers.find(x=>x.ma_kh===b.dataset.address);
    modal("Địa chỉ của "+r.ho_ten,form(input("dia_chi","Địa chỉ mới","text",`maxlength="200" value="${esc(r.dia_chi)}"`),"Lưu địa chỉ"));
    bindForm($("#dialog form"),async d=>refresh((await api(`customers/${encodeURIComponent(r.ma_kh)}/address`,"PATCH",d)).message));
  };
}
const accountOpts=kind=>options(state.accounts.filter(r=>r.loai===kind),"so_tk",r=>`${r.so_tk} · ${r.ho_ten}`);
const staffOpts=sales=>options(state.employees.filter(r=>!sales||r.vi_tri==="KINH_DOANH"),"ma_nv",r=>`${r.ma_nv} · ${r.ho_ten}`);
const positive='min="1" step="1"', nonnegative='min="0" step="1"';
function accounts(){
  page.innerHTML=header("Tài khoản","",button("new-account","Mở tài khoản"))+`<div class="panel">${searchbar("Tìm số tài khoản, mã hoặc tên khách hàng")}</div>`;
  searchable(state.accounts,[["so_tk","Số TK","code"],["ho_ten","Chủ tài khoản"],["loai","Loại","tag"],["so_du","Số dư khả dụng (₫)","money"],["ngay_mo","Ngày mở","date"],["nguoi_mo","Nhân viên mở"],["","",r=>`<button class="linkbutton" data-stmt="${esc(r.so_tk)}">Sao kê</button>`]],["so_tk","ho_ten","ma_kh"]);
  $("#new-account").onclick=()=>{
    const kind='<option value="GUI">Gửi tiền</option><option value="TD">Tín dụng</option>';
    const fields=input("so_tk","Số tài khoản","text",'maxlength="20" pattern="[A-Za-z0-9_\\-]+"')+
      select("loai","Loại tài khoản",kind)+select("ma_kh","Chủ tài khoản",options(state.customers,"ma_kh",r=>`${r.ma_kh} · ${r.ho_ten}`))+select("nv_mo","Nhân viên kinh doanh",staffOpts(true))+'<div id="subfields" class="fieldgrid wide"></div>';
    modal("Mở tài khoản",form(fields,"Mở tài khoản"));
    const kindInput=$("#dialog select[name=loai]");
    const change=()=>{$("#subfields").innerHTML=kindInput.value==="TD"?input("han_muc","Hạn mức tín dụng (₫)","number",positive):
        input("tien_gui_dau","Tiền gửi lần đầu (₫)","number",nonnegative)+input("du_toi_thieu","Số dư tối thiểu (₫)","number",nonnegative)+input("lai_thang","Lãi suất tháng (%)","number",'min="0" max="100" step="0.001"');};
    kindInput.onchange=change;change();
    bindForm($("#dialog form"),async d=>refresh((await api("accounts","POST",d)).message));
  };
  $("#directory").onclick=async e=>{const b=e.target.closest("[data-stmt]");if(!b)return;
    try{const code=b.dataset.stmt, s=await api(`accounts/${encodeURIComponent(code)}/statement`);
      const info=state.accounts.find(r=>r.so_tk===code);
      const detail=info.loai==="GUI"?`Tiền gửi đầu ${money(info.tien_gui_dau)} ₫ · Tối thiểu ${money(info.du_toi_thieu)} ₫ · Lãi ${Number(info.lai_thang)}%/tháng`:
        `Hạn mức ${money(info.han_muc)} ₫ · Dư nợ ${money(BigInt(info.han_muc)-BigInt(info.so_du))} ₫`;
      modal("Sao kê "+code,`<p>${esc(info.ho_ten)} · Mở ngày ${fmtDay(info.ngay_mo)}</p><p class="help">${detail}</p>`+
        table(s.rows,[["luc","Thời điểm","time"],["loai","Nghiệp vụ","tag"],["tk_gui","TK gửi"],["tk_td","TK tín dụng"],["so_tien","Số tiền (₫)","money"]]));
    }catch(err){notify(err.message,true);}
  };
}
function employees(){
  page.innerHTML=header("Nhân viên chi nhánh")+`<div class="panel">${searchbar("Tìm nhân viên theo tên hoặc mã")}</div>`;
  searchable(state.employees,[["ma_nv","Mã NV","code"],["ho_ten","Họ và tên"],["vi_tri","Vị trí","tag"],["bac_nghe","Bậc nghề"],["tham_nien","Thâm niên (năm)"],["ngay_vao_lam","Ngày vào làm","date"],["cmt","CMT / CCCD"],["ngay_sinh","Ngày sinh","date"],["dia_chi","Địa chỉ"]],["ma_nv","ho_ten"]);
}
function transactions(){
  const needsGui=txnKind!=="CHI",needsTd=txnKind!=="NAP";
  const fields=(needsGui?select("tk_gui",txnKind==="TRA"?"Tài khoản gửi trích tiền":"Tài khoản nhận tiền nộp",accountOpts("GUI"),true):"")+
    (needsTd?select("tk_td","Tài khoản tín dụng",accountOpts("TD"),true):"")+
    input("so_tien","Số tiền (₫)","number",positive)+
    select("nv_ho_tro","Nhân viên hỗ trợ",'<option value="">Tự thực hiện</option>'+staffOpts(false)).replace(" required","");
  page.innerHTML=header("Giao dịch")+`<div class="panel inline-form"><div class="tabs">${["TRA","CHI","NAP"].map(k=>`<button data-kind="${k}" class="${k===txnKind?"active":""}">${k==="TRA"?"Thanh toán dư nợ":k==="CHI"?"Chi tiêu tín dụng":"Nộp tiền gửi"}</button>`).join("")}</div>
    <div id="balance" class="help"></div>${form(fields,txnKind==="TRA"?"Xác nhận thanh toán":txnKind==="CHI"?"Ghi nhận chi tiêu":"Xác nhận nộp tiền")}</div>`;
  page.querySelectorAll("[data-kind]").forEach(b=>b.onclick=()=>{txnKind=b.dataset.kind;notify("");transactions();});
  const f=page.querySelector("form");
  function balance(){
    const find=name=>state.accounts.find(a=>a.so_tk===f.elements[name]?.value);
    const a=find("tk_gui"),b=find("tk_td"), info=[];
    if(a)info.push(`Số dư tiền gửi ${money(a.so_du)} ₫ · Mức tối thiểu ${money(a.du_toi_thieu)} ₫`);
    if(b)info.push(`Dư nợ ${money(BigInt(b.han_muc)-BigInt(b.so_du))} ₫ · Tín dụng khả dụng ${money(b.so_du)} ₫`);
    if(a&&b&&a.ma_kh!==b.ma_kh)info.push(`${esc(a.ho_ten)} thanh toán hộ ${esc(b.ho_ten)}.`);
    $("#balance").innerHTML=info.join("<br>") || "Cần mở tài khoản tương ứng để giao dịch.";
  }
  f.onchange=balance;balance();
  let key=null,signature="";
  bindForm(f,async d=>{
    if(JSON.stringify(d)!==signature || !key){signature=JSON.stringify(d);key=crypto.randomUUID();}
    const result=await api("transactions","POST",{...d,loai:txnKind,ma_gd:key});
    await refresh(`${result.message} Mã giao dịch ${result.ma_gd}`);
  });
}
const reportInfo={
  salary:["Lương kinh doanh",[["ma_nv","Mã NV","code"],["ho_ten","Nhân viên"],["so_td","TK tín dụng"],["so_gui","TK gửi"],["tong_gui_dau","Tổng gửi lần đầu (₫)","money"],["luong","Lương nghiệp vụ (₫)","money"]]],
  activity:["Giao dịch tín dụng",[["ho_ten","Người thực hiện"],["so_tk","TK tín dụng","code"],["chu_tk","Chủ TK tín dụng"],["so_luot","Số lượt"],["chi_tieu","Chi tiêu (₫)","money"],["thanh_toan","Thanh toán (₫)","money"],["tong_giao_dich","Tổng giao dịch (₫)","money"]]],
  debt:["Dư nợ",[["so_tk","TK tín dụng","code"],["ho_ten","Chủ tài khoản"],["han_muc","Hạn mức (₫)","money"],["kha_dung","Khả dụng (₫)","money"],["du_no","Dư nợ (₫)","money"]]],
  top:["Top 10 tiền gửi",[["ma_kh","Mã KH","code"],["ho_ten","Khách hàng"],["so_tk_gui","Số TK gửi"],["tong_gui","Tổng tiền gửi (₫)","money"]]]
};
function exportReport(){
  if(!reportCache)return;
  const cell=v=>{let t=String(v??"");if(/^[=+@\-\t\r]/.test(t))t="'"+t;return '"'+t.replaceAll('"','""')+'"';};
  const {rows,cols}=reportCache;
  const csv=[cols.map(c=>cell(c[1])),...rows.map(r=>cols.map(c=>cell(r[c[0]])))].map(r=>r.join(",")).join("\r\n");
  const url=URL.createObjectURL(new Blob(["\ufeff",csv],{type:"text/csv;charset=utf-8"}));
  const a=document.createElement("a");a.href=url;a.download=`bao-cao-${report}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function reports(){
  const n=++reportSeq;reportCache=null;
  const name=report, cols=reportInfo[name][1];
  const filter=name==="salary"?input("month","Tháng báo cáo","month",`value="${esc(period.month)}"`):
    name==="activity"?input("from","Từ ngày","date",`value="${esc(period.from)}"`)+input("to","Đến ngày","date",`value="${esc(period.to)}"`):"";
  page.innerHTML=header("Báo cáo chi nhánh")+`<div class="tabs">${Object.entries(reportInfo).map(([key,v])=>`<button data-report="${key}" class="${key===name?"active":""}">${v[0]}</button>`).join("")}</div><article class="panel"><div class="sectionhead"><h2>${reportInfo[name][0]}</h2>${button("export","Xuất CSV","secondary")}</div>${filter?`<form class="filters">${filter}<button class="secondary" type="submit">Xem kết quả</button></form>`:""}<div id="results">Đang tra cứu…</div></article>`;
  $("#export").disabled=true;$("#export").onclick=exportReport;
  page.querySelectorAll("[data-report]").forEach(b=>b.onclick=()=>{report=b.dataset.report;reports();});
  const f=page.querySelector("form");if(f)f.onsubmit=e=>{e.preventDefault();Object.assign(period,Object.fromEntries(new FormData(f)));reports();};
  try{
    const rows=await api(`reports/${name}?${new URLSearchParams(period)}`);
    if(n!==reportSeq||route!=="reports")return;
    $("#results").innerHTML=table(rows,cols);reportCache={rows,cols};$("#export").disabled=false;
  }catch(err){if(n===reportSeq&&route==="reports")$("#results").innerHTML=`<p class="error">${esc(err.message)}</p>`;}
}
async function navigate(){
  const n=++seq; route=location.hash.slice(1);if(!routes[route])route="home";
  notify("");if(dialog.open)dialog.close();$("#crumb").textContent=routes[route];
  document.querySelectorAll("[data-nav]").forEach(a=>{if(a.dataset.nav===route)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");});
  page.setAttribute("aria-busy","true");
  page.innerHTML='<p class="muted">Đang tải dữ liệu…</p>';
  try{
    const paths=route==="home"?["overview","reports/top"]:route==="customers"?["customers"]:route==="employees"?["employees"]:
      ["accounts","transactions"].includes(route)?["accounts","employees",...(route==="accounts"?["customers"]:[])]:[];
    const values=await Promise.all(paths.map(p=>api(p)));if(n!==seq)return;
    paths.forEach((p,i)=>state[p==="reports/top"?"top":p]=values[i]);
    const today=state.overview?.totals.hom_nay || new Intl.DateTimeFormat("sv-SE",{timeZone:"Asia/Ho_Chi_Minh"}).format(new Date());
    if(!period.month)period={month:today.slice(0,7),from:today.slice(0,7)+"-01",to:today};
    $("#today").textContent=fmtDay(today);
    await ({home,customers,accounts,employees,transactions,reports}[route])();
  }catch(err){if(n===seq){page.innerHTML=header(routes[route])+`<div class="error">${esc(err.message)}</div>${button("retry","Thử lại","secondary")}`;$("#retry").onclick=navigate;}}
  finally{if(n===seq)page.setAttribute("aria-busy","false");}
}
window.addEventListener("hashchange",navigate);navigate();
