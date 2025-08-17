import fetch from "node-fetch";

const base = process.env.API_BASE_URL || "http://localhost:8080";

async function main(){
  const h = await fetch(`${base}/health`).then(r=>r.json()).catch(e=>({error:String(e)}));
  console.log("health:", h);

  const start = await fetch(`${base}/scraper/start`, {
    method:"POST",
    headers:{ "content-type":"application/json" },
    body: JSON.stringify({ listing_type:"sale", max_pages:1, delay_ms:10, headful:false })
  }).then(r=>r.json()).catch(e=>({error:String(e)}));
  console.log("scraper.start:", start);
}
main();
