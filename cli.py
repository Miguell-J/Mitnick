from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
import main
import os

console = Console()

def main_loop(app):
    os.system("clear")  # ou "cls" no Windows
    console.print(Panel.fit("[bold green]Welcome to Mitnick — your hacker agent![/bold green]\nType 'exit' to leave."))
    console.print("[bold magenta]Ex: scan the IP 11.22.33.44 or run whois on google.com[/bold magenta]")

    state = {
        "question": "",
        "target": "",
        "response": "",
        "action": "",
        "recon_data": {},
        "scan_results": "",
        "vuln_analysis": [],
        "history": []
    }

    while True:
        user_input = Prompt.ask("[bold cyan]Type your command[/bold cyan]")
        if user_input.lower() in ["exit", "quit"]:
            console.print("[bold red]Exiting... Bye![/bold red]")
            break

        state["question"] = user_input
        if "http" in user_input or "." in user_input:
            state["target"] = user_input.split()[-1]

        try:
            state = app.invoke(state)
        except Exception as e:
            console.print(f"[bold red]Error in the command processing:[/bold red] {e}")
            continue

        response_text = state.get("response", "No agent response available.")
        console.print(Panel(Text(response_text, style="bold white"), title="[bold yellow]Mitnick Response[/bold yellow]"))

        if len(state["history"]) > 0:
            console.print(f"[dim][📜] History: {len(state['history'])} registered events[/dim]")

if __name__ == "__main__":
    app = main.app
    main_loop(app)

