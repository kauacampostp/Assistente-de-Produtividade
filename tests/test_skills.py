from skills.loader import get_skill_catalog, load_skill

catalog = get_skill_catalog()

print("Skills disponíveis:")

for skill in catalog:
    print(f"- {skill['name']}: {skill['description']}")

print("\nTeste de carregamento:")

content = load_skill("analise-documental")
print(content[:200])
