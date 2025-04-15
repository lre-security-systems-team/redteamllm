from .redteamagent import RedTeamAgent

def main():
    agent = RedTeamAgent("Create a POSIX shell in C")
    a = agent.plan()

if __name__ == "__main__":
    main()