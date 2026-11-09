#!/usr/bin/env python3
"""H1: P7 com perda esperada Poisson, tabelada por estacao e estoque."""
import datetime as dt
import importlib.util
import json
import math
import os
import sys

spec=importlib.util.spec_from_file_location("p2_base",os.path.join("..","p2_perda_marginal","main.py"))
p2=importlib.util.module_from_spec(spec); spec.loader.exec_module(p2)
MAX_MOV,MAX_Q,TOP=3,10,5

def perda_cauda(lam, limite):
    """E[(X-limite)+] para X Poisson(lam), por recorrencia de probabilidades."""
    if lam <= 0: return 0.0
    p=math.exp(-lam); perda=0.0
    fim=max(limite+25,int(lam+12*math.sqrt(lam)+20))
    for k in range(1,fim+1):
        p*=lam/k
        if k>limite: perda+=(k-limite)*p
    return perda

def decidir(dados):
    try:
        with open(p2.ARQ_CACHE,encoding="utf-8") as f: perfis=json.load(f)["perfis"]
    except (OSError,ValueError,KeyError): return []
    agora=dt.datetime.fromisoformat(dados["timestamp"]); prox=agora+dt.timedelta(hours=1)
    estado={e["station_id"]:dict(e) for e in dados["estacoes"] if e["status"]=="active"}
    def perfil(sid,t):
        r,a=perfis.get(p2.chave(sid,t.hour,t.weekday()),(0.0,0.0))
        return (0.0 if t.hour<5 or t.hour>=22 else r),a
    # Tabelas por estoque evitam somas Poisson dentro da busca combinatoria.
    tabelas={}
    for e in estado.values():
        r0,a0=perfil(e["station_id"],agora); r1,a1=perfil(e["station_id"],prox)
        atual=[perda_cauda(r0,b)+perda_cauda(a0,e["capacity"]-b) for b in range(e["capacity"]+1)]
        futuro=[perda_cauda(r1,b)+perda_cauda(a1,e["capacity"]-b) for b in range(e["capacity"]+1)]
        tabelas[e["station_id"]]=(atual,futuro,r0,a0)
    def risco(e,b):
        atual,futuro,r,a=tabelas[e["station_id"]]
        b1=min(e["capacity"],max(0,int(round(b-r+a))))
        return atual[b]+futuro[b1]
    movs=[]
    for _ in range(MAX_MOV):
        melhor=None
        for q in range(1,MAX_Q+1):
            osrc=[];odst=[]
            for e in estado.values():
                b=e["available_bikes"]
                if b>=q: osrc.append((risco(e,b-q)-risco(e,b),e["station_id"]))
                if e["available_docks"]>=q: odst.append((risco(e,b)-risco(e,b+q),e["station_id"]))
            osrc.sort();odst.sort(reverse=True)
            for custo,o in osrc[:TOP]:
                for beneficio,d in odst[:TOP]:
                    if o!=d:
                        cand=(beneficio-custo,q,o,d)
                        if melhor is None or cand>melhor: melhor=cand
        if melhor is None or melhor[0]<=1e-9: break
        _,q,o,d=melhor; origem,destino=estado[o],estado[d]
        movs.append({"origem":o,"destino":d,"quantidade":q})
        origem["available_bikes"]-=q;origem["available_docks"]+=q
        destino["available_bikes"]+=q;destino["available_docks"]-=q
    return movs
def main():
    if "--preparar" in sys.argv:return p2.preparar()
    if "--passo" in sys.argv:
        try: movs=decidir(json.load(sys.stdin))
        except Exception as e: print(repr(e),file=sys.stderr);movs=[]
        print(json.dumps({"movimentacoes":movs}));return 0
    return 0
if __name__=="__main__":raise SystemExit(main())
