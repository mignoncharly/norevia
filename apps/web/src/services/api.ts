import type { LocationOption, RankingRequest, RankingResponse } from "@/types/api";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
async function request<T>(path:string, init?:RequestInit):Promise<T>{
  const response=await fetch(`${baseUrl}${path}`,{...init,headers:{"Content-Type":"application/json",...init?.headers}});
  if(!response.ok){const body=await response.json().catch(()=>null) as {error?:{messageKey?:string}}|null;throw new Error(body?.error?.messageKey??"errors.network");}
  return response.json() as Promise<T>;
}
export const api={
  locations:()=>request<LocationOption[]>("/locations?type=city&country=DE"),
  rank:(payload:RankingRequest)=>request<RankingResponse>("/rankings",{method:"POST",body:JSON.stringify(payload)}),
};
