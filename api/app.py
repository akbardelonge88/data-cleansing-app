<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>CLI Data Cleansing App</title>

<!-- SheetJS for Excel -->
<script src="https://cdn.jsdelivr.net/npm/xlsx/dist/xlsx.full.min.js"></script>

<style>
body { font-family: Arial, sans-serif; background:#f4f6fb; margin:0; padding:20px }
.card { background:white; padding:20px; border-radius:10px; box-shadow:0 5px 15px rgba(0,0,0,0.08); margin-bottom:20px }
h2 { margin-top:0 }
input, button { padding:8px; margin:5px 0; width:100% }
button { background:#2b6ef2; color:white; border:none; border-radius:6px; cursor:pointer }
button:hover { background:#1f4fd8 }
table { border-collapse: collapse; width:100%; font-size:12px }
th, td { border:1px solid #ddd; padding:6px; text-align:left }
th { background:#2b6ef2; color:white; position:sticky; top:0 }
.hidden { display:none }
.footer { text-align:center; font-size:12px; color:#777; margin-top:30px }
</style>
</head>
<body>

<div id="loginCard" class="card">
  <h2>🔐 Login Aplikasi</h2>
  <input type="text" id="username" placeholder="Username">
  <input type="password" id="password" placeholder="Password">
  <button onclick="login()">Login</button>
  <p id="loginMsg" style="color:red;"></p>
</div>

<div id="appCard" class="card hidden">
  <h2>📊 Data Cleansing CLI</h2>
  <input type="file" id="fileInput" accept=".xlsx"/>
  <button onclick="processFile()">🚀 Proses Data</button>
  <button onclick="downloadExcel()">📥 Download Hasil</button>
  <button onclick="logout()">Logout</button>
</div>

<div id="tableCard" class="card hidden">
  <h2>📋 Hasil Transformasi</h2>
  <div style="overflow:auto; max-height:500px;">
    <table id="resultTable"></table>
  </div>
</div>

<div class="footer">© 2026 - Muhamad Akbar</div>

<script>
const USER = "admin";
const PASS = "admin123";
let resultData = [];

function login(){
  const u = document.getElementById("username").value;
  const p = document.getElementById("password").value;
  if(u===USER && p===PASS){
    document.getElementById("loginCard").classList.add("hidden");
    document.getElementById("appCard").classList.remove("hidden");
  } else {
    document.getElementById("loginMsg").innerText = "Username atau password salah";
  }
}

function logout(){
  location.reload();
}

function splitPhones(str,i){
  if(!str) return "";
  return str.split(";")[i]?.trim().replace(/^0/,"") || "";
}

function extractAmount(detail, cli){
  if(!detail || !cli) return 0;
  const regex = new RegExp(cli + "=([0-9]+)");
  const m = detail.match(regex);
  return m ? parseInt(m[1]) : 0;
}

function extractVA(row, keyword){
  const cols = [
    "va_number_adt_indodana","va_number_adt_blibli","va_number_adt_tiket",
    "va_number_imf_indodana","va_number_imf_blibli","va_number_imf_tiket"
  ];
  let res=[];
  cols.forEach(c=>{
    if(row[c]){
      row[c].split(";").forEach(v=>{
        if(v.toUpperCase().includes(keyword)) res.push(v.trim()+";");
      })
    }
  });
  return res.join("\n");
}

// ================= PAYMENT PARSER =================
function parsePayments(history, collateral){
  if(!history || !collateral) return {};

  let trxList = collateral.match(/TRX-[A-Z0-9]+/g) || [];
  let map = {};

  trxList.forEach(trx=>{
    let regex = new RegExp(trx + " Payment.*?Date ([0-9-]+), Amount ([0-9]+)", "g");
    let m;
    while((m = regex.exec(history)) !== null){
      let key = m[1];
      if(!map[key]) map[key]=0;
      map[key]+=parseInt(m[2]);
    }
  });

  let sorted = Object.entries(map).sort((a,b)=> new Date(b[0]) - new Date(a[0]));
  return {
    d1: sorted[0]?.[0]||"", a1: sorted[0]?.[1]||"",
    d2: sorted[1]?.[0]||"", a2: sorted[1]?.[1]||"",
    d3: sorted[2]?.[0]||"", a3: sorted[2]?.[1]||"",
  };
}

// ================= MAIN PROCESS =================
function processFile(){
  const file = document.getElementById("fileInput").files[0];
  if(!file) return alert("Upload file dulu bro");

  const reader = new FileReader();
  reader.onload = function(e){
    const wb = XLSX.read(e.target.result, {type:'binary'});
    const sheet = wb.Sheets[wb.SheetNames[0]];
    const data = XLSX.utils.sheet_to_json(sheet);

    let rows=[];
    const cliMap = [
      ["CLI_indodana_2_contain_adt","product_CLI_indodana_2_adt"],
      ["CLI_blibli_3_contain_adt","product_CLI_blibli_3_adt"],
      ["CLI_tiket_4_contain_adt","product_CLI_tiket_4_adt"],
      ["CLI_indodana_2_contain_imf","product_CLI_indodana_2_imf"],
      ["CLI_blibli_3_contain_imf","product_CLI_blibli_3_imf"],
      ["CLI_tiket_4_contain_imf","product_CLI_tiket_4_imf"]
    ];

    data.forEach(r=>{
      cliMap.forEach(m=>{
        let cli = r[m[0]];
        let prod = r[m[1]];
        if(cli){
          let pay = parsePayments(r["payments_history_cli_indodana_2"], prod);
          rows.push({
            CLIENT_NAME:"INDODANA MULTI FINANCE",
            CLIENT_CODE:"CLI00057",
            ASSIGNMENT_DATE:r.start_date,
            ASSIGNED_TO: None,
            BATCH: r["batch_import"],
            CUSTOMER_ID:cli,
            ADDRESS: None,
            AGREEMENT_NO: r["orderId_DC"],
            CITY: None,
            CUSTOMER_NAME:(r.name||"").toUpperCase(),
            PROVINCE: None,
            GENDER: r["applicantGender"],
            MOBILE_NO:splitPhones(r.PhoneNumber,0),
            DATE_OF_BIRTH: r["dob"],
            MOBILE_NO_2:splitPhones(r.PhoneNumber,1),
            EMAIL:r.applicantPersonalEmail,
            PRODUCT:m[0].includes("adt")?"ADT":"IMF",
            TENOR:r.tenure,
            SUB_PRODUCT: m["cli_col"],
            RENTAL: r["angsuran_per_bulan"],
            DISBURSE_DATE: None,
            OVD_DAYS: r["max_current_dpd"],
            LOAN_AMOUNT:extractAmount(r.total_hutang_detail,cli),
            BUCKET: None,
            DUEDATE: r["tgl_jatuh_tempo"],
            AMOUNT_OVERDUE: None,
            OS_PRINCIPAL:extractAmount(r.pokok_tertunggak_detail,cli),
            LAST_PAYMENT_DATE: pay.d1,
            OS_INTEREST: None,
            LAST_PAYMENT_AMOUNT: pay.a1,
            OS_CHARGES:extractAmount(r.latefee_detail,cli),
            PAID_OFF_WITH_DISCOUNT: None,
            TOTAL_OUTSTANDING:extractAmount(r.total_outstanding_detail,cli),
            FLAG_DISCOUNT": None,
            BCA_VA:extractVA(r,"BCA"),
            INDOMARET: None,
            MANDIRI_VA:extractVA(r,"MANDIRI"),
            ALFAMART: None,
            BRI_VA: None,
            PERMATA_VA:extractVA(r,"PERMATA"),
            COMPANY_NAME:r.current_company_name,
            ADDRESS_COMPANY: None, 
            POSITION:r.jobTitle,
            OFFICE_PHONE_NO: r["currentCompanyPhoneNumber"],
            EMERGENCY_NAME_1: r["mothername"],
            EMERGENCY_NAME_2: split_refs(r["referenceFullName"], 0),
            EMERGENCY_RELATIONSHIP_1: "Ibu Kandung",
            EMERGENCY_RELATIONSHIP_2": split_refs(r["referenceRelationship"], 0),
            EMERGENCY_PHONE_NO_1: None,
            EMERGENCY_PHONE_NO_2: r["referenceMobilePhoneNumber"],
            EMERGENCY_ADDRESS_1: None,
            EMERGENCY_ADDRESS_2: None,
            REMARKS 1: None,
            REMARKS 2: None,
            REMARKS 3: None,
            COLLATERAL_DESCRIPTION:prod,
            CERTIFICATE_NO / POLICE_NO: None,
            AGENT: None,
            "2nd_Last_Payment_Date":pay.d2,
            "2nd_Last_Payment_Amount":pay.a2,
            "3rd_Last_Payment_Date":pay.d3,
            "3rd_Last_Payment_Amount":pay.a3
          });
        }
      });
    });

    resultData = rows;
    renderTable(rows);
  };
  reader.readAsBinaryString(file);
}

function renderTable(data){
  document.getElementById("tableCard").classList.remove("hidden");
  let table=document.getElementById("resultTable");
  table.innerHTML="";
  let header="<tr>"+Object.keys(data[0]).map(h=>`<th>${h}</th>`).join("")+"</tr>";
  table.innerHTML+=header;
  data.forEach(r=>{
    let row="<tr>"+Object.values(r).map(v=>`<td>${v}</td>`).join("")+"</tr>";
    table.innerHTML+=row;
  });
}

function downloadExcel(){
  if(resultData.length===0) return alert("Belum ada data bro");
  const ws = XLSX.utils.json_to_sheet(resultData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Result");
  XLSX.writeFile(wb, "hasil_final_cli.xlsx");
}
</script>

</body>
</html>