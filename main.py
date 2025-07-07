from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

import os
from langchain.chat_models import init_chat_model

import subprocess

from langchain_openai import ChatOpenAI

"""
Aqui chegamos a mais um episodio de Miguel se irritando com o código por que não entender nada sobre o porque está dando erro.

Bom, aqui vamos criar um agente de IA com LangGraph, o objetivo é criar um assistente que vai nos ajudar a automatizar e acelerar o nosso hacking
Principalmente agora que começaremos a entrar em areas como bug bounty, ter um Mitinik funcional e operante será um auxilio gigante nessa jornada de hacking

Temos uma noção clara (inicial) de como o agente vai se comportar:
[recebe comando] -> [decide o que fazer] -> [faz scan, exploit, enum, recon] -> [Faz o report] -> [retorna output]

Show, então temos que resolver algumas coisas a principio:

1- Definir estados
2- Definir o LLM (cerebro)
3- Definir transições
4- Definir ferramentas

Vamos usar o langgraph para isso


"""

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    api_key=os.getenv("OPENAI_KEY")  # nosso cerebro
)

# criamos o stado, esse deve ser melhorado depois, mas por agora está bom, ele vai ter um target e uma response
class State(TypedDict):
    question: str
    target: str
    response: str
    action: str
    recon_data: dict
    scan_results: str
    vuln_analysis: list
    enum_results: str
    history: list[str]

def decide_and_update(state: State) -> State:
    action = classify_action(state["question"])
    state["action"] = action
    return state


def classify_action(question: str) -> str:
    resposta = llm.invoke(f"""You are a cybersecurity agent.
    You receive commands from the user in natural language.
    Your task is to CLASSIFY the command as one of these actions:

    - recon → for target reconnaissance
    - scan → for scanning ports or services 
    - exploit → for exploiting known vulnerabilities 
    - enum → for enumarating hidden files or directories of the target
    - report → for generating a report or summary
    - other → if none of the above options are used

    Command: "{question}"

    Answer with just ONE word: recon, scan, exploit, enum, report or other.
    """)
    
    return resposta.content.strip().lower()




#---------------SCAN TOOLS-------------------
def scan_port_nmap(state: State) -> State:
    target = state["target"]
    result = subprocess.run(
        ["nmap", "-T4", "-Pn", target],
        capture_output=True,
        text=True
    )
    state["scan_results"] = result.stdout
    state["history"].append(result.stdout)
    return state

def scan_rustscan(state: State) -> State:
    target = state["target"]
    result = subprocess.run(
        ["rustscan", "-a", target, "-A"],
        capture_output=True,
        text=True
    )
    state["scan_results"] = result.stdout
    state["history"].append(result.stdout)
    return state

def scan_httpx(state: State) -> State:
    target = state["target"]
    result = subprocess.run(
        ["httpx", "-l", target],
        capture_output=True,
        text=True
    )
    state["scan_results"] = result.stdout
    state["history"].append(result.stdout)
    return state

def scan_shodan(state: State) -> State:
    target = state["target"]
    result = subprocess.run(
        ["shodan", "host", target],
        capture_output=True,
        text=True
    )
    state["scan_results"] = result.stdout
    state["history"].append(result.stdout)
    return state

#---master--
def scan(state: State) -> State:
    prompt = f"""You are a scanning agent. Choose the best tool for this question:

"{state['question']}"

Options:
- nmap
- rustscan
- httpx
- shodan

Answer with only ONE word.
    """
    resposta = llm.invoke(prompt).content.strip().lower()

    if resposta == "nmap":
        return scan_port_nmap(state)
    elif resposta == "rustscan":
        return scan_rustscan(state)
    elif resposta == "httpx":
        return scan_httpx(state)
    elif resposta == "shodan":
        return scan_shodan(state)
    else:
        state["history"].append("Scan: ferramenta não reconhecida.")
        return state



#------------ENUM TOOLS---------------------
def enum_nikto(state: State) -> State:
    target = state["target"]
    result = subprocess.run(
        ["nikto", "-h", target],
        capture_output=True,
        text=True
    )
    state["enum_results"] = result.stdout
    state["history"].append(result.stdout)
    return state

def enum_dirb(state: State) -> State:
    target = state["target"]
    result = subprocess.run(
        ["dirb", target],
        capture_output=True,
        text=True
    )
    state["enum_results"] = result.stdout
    state["history"].append(result.stdout)
    return state

def enum_whatweb(state: State) -> State:
    target = state["target"]
    result = subprocess.run(
        ["whatweb", target],
        capture_output=True,
        text=True
    )
    state["enum_results"] = result.stdout
    state["history"].append(result.stdout)
    return state

def enum_gobuster(state: State) -> State:
    target = state["target"]
    result = subprocess.run(
        ["gobuster", "-w", "wordlist.txt", target],
        capture_output=True,
        text=True
    )
    state["enum_results"] = result.stdout
    state["history"].append(result.stdout)
    return state

#---master--
def enum(state: State) -> State:
    prompt = f"""You are a enumeration agent. Choose the best tool for this question:

"{state['question']}"

Options:
- nikto
- dirb
- whatweb
- gobuster

Answer with only ONE word.
    """
    resposta = llm.invoke(prompt).content.strip().lower()

    if resposta == "nikto":
        return enum_nikto(state)
    elif resposta == "dirb":
        return enum_dirb(state)
    elif resposta == "whatweb":
        return enum_whatweb(state)
    elif resposta == "gobuster":
        return enum_gobuster(state)
    else:
        state["history"].append("Enum: ferramenta não reconhecida.")
        return state







#------------EXPLOIT TOOLS-------------------
def exploit_sqlmap(state: State) -> State:
    result = subprocess.run(["sqlmap", "-u", state["target"], "--batch", "--crawl=1"], capture_output=True, text=True)
    state["response"] = result.stdout
    state["history"].append("Exploit - sqlmap: OK")
    return state

def exploit_exploitdb(state: State) -> State:
    result = subprocess.run(["searchsploit", state["target"]], capture_output=True, text=True)
    state["response"] = result.stdout
    state["history"].append("Exploit - exploitdb: OK")
    return state

def exploit_commix(state: State) -> State:
    result = subprocess.run(["commix", "--url", state["target"]], capture_output=True, text=True)
    state["response"] = result.stdout
    state["history"].append("Exploit - commix: OK")
    return state

def exploit_xsser(state: State) -> State:
    result = subprocess.run(["xsser", "--url", state["target"]], capture_output=True, text=True)
    state["response"] = result.stdout
    state["history"].append("Exploit - xsser: OK")
    return state

#---master---
def exploit(state: State) -> State:
    prompt = f"""You are a exploit agent. Choose the best tool for this question:

"{state['question']}"

Options:
- sqlmap
- exploitdb
- commix
- xsser

Answer with only ONE word.
    """
    
    resposta = llm.invoke(prompt).content.strip().lower()

    if resposta == "sqlmap":
        return exploit_sqlmap(state)
    elif resposta == "exploitdb":
        return exploit_exploitdb(state)
    elif resposta == "commix":
        return exploit_commix(state)
    elif resposta == "xsser":
        return exploit_xsser(state)
    else:
        state["history"].append("Exploit: ferramenta não reconhecida.")
        return state






# -------------RECON TOOLS-----------------
def recon_whois(state: State) -> State:
    result = subprocess.run(["whois", state["target"]], capture_output=True, text=True)
    state["recon_data"]["whois"] = result.stdout
    state["history"].append("Recon - whois: OK")
    return state

def recon_subfinder(state: State) -> State:
    result = subprocess.run(["subfinder", "-d", state["target"]], capture_output=True, text=True)
    state["recon_data"]["subfinder"] = result.stdout
    state["history"].append("Recon - subfinder: OK")
    return state

def recon_amass(state: State) -> State:
    result = subprocess.run(["amass", "enum", "-d", state["target"]], capture_output=True, text=True)
    state["recon_data"]["amass"] = result.stdout
    state["history"].append("Recon - amass: OK")
    return state

def recon_crt_sh(state: State) -> State:
    result = subprocess.run(["sh", "crt.sh", "-d", state["target"]], capture_output=True, text=True)
    state["recon_data"]["crt_sh"] = result.stdout
    state["history"].append("Recon - crt.sh: OK")
    return state

def recon_censys(state: State) -> State:
    result = subprocess.run(["censys", "search", state["target"]], capture_output=True, text=True)
    state["recon_data"]["censys"] = result.stdout
    state["history"].append("Recon - censys: OK")
    return state

def recon_nslookup(state: State) -> State:
    result = subprocess.run(["nslookup", state["target"]], capture_output=True, text=True)
    state["recon_data"]["nslookup"] = result.stdout
    state["history"].append("Recon - nslookup: OK")
    return state

#--master--
def recon(state: State) -> State:
    prompt = f"""
You are a reconnaissance agent. Choose the best tool for this question:

"{state['question']}"

Options:
- whois
- subfinder
- amass
- nslookup
- crt.sh
- censys

Answer with only ONE word.
"""

    resposta = llm.invoke(prompt).content.strip().lower()

    if resposta == "whois":
        return recon_whois(state)
    elif resposta == "subfinder":
        return recon_subfinder(state)
    elif resposta == "amass":
        return recon_amass(state)
    elif resposta == "nslookup":
        return recon_nslookup(state)
    elif resposta == "crt.sh":
        return recon_crt_sh(state)
    elif resposta == "censys":
        return recon_censys(state)
    else:
        state["history"].append("Recon: ferramenta não reconhecida.")
        return state




 



#----------LOG & REPORT TOOLS-----------------
def report(state: State) -> State:
    with open("logs.txt", "w") as file_logs:
        file_logs.write("\n".join(state["history"]))

    resumo = llm.invoke(f"""
You are a security agent. Here is the history of the attack:

{chr(10).join(state["history"])}

Summarize actions, highlight vulnerabilities, and suggest next steps.
""")

    state["response"] = resumo.content
    return state





graph = StateGraph(State)


graph.add_node("recon", recon) 
graph.add_node("scan", scan)
graph.add_node("enum", enum)
graph.add_node("exploit", exploit)
graph.add_node("report", report)

graph.add_node("decide_action", decide_and_update)


graph.add_conditional_edges(
    "decide_action",
    lambda state: state["action"],  # retorna só o nome do próximo nó
    {
        "recon": "recon",
        "scan": "scan",
        "enum": "enum",
        "exploit": "exploit",
        "report": "report",
        "other": END
    }
)

graph.set_entry_point("decide_action")

graph.add_edge("recon", "report")
graph.add_edge("enum", "report")
graph.add_edge("scan", "report")
graph.add_edge("exploit", "report")
graph.add_edge("report", END)



app = graph.compile()
