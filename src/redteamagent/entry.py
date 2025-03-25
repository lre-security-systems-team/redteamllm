from .redteamagent import RedTeamAgent

def main():
    agent = RedTeamAgent("Create a python script to calculate fibonnacci in a server web")
    a = agent.plan()
    print(a)

if __name__ == "__main__":
    main()
    