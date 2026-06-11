from .redteamagent import RedTeamAgent

def main():
    agent = RedTeamAgent(input("Enter the task to decompose : "))
    a = agent.plan()

if __name__ == "__main__":
    main()