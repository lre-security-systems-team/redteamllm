from .redteamagent import RedTeamAgent

def main():
    agent = RedTeamAgent("I want you to compromise the machine with ip '192.168.1.45'")
    a = agent.plan()

if __name__ == "__main__":
    main()