import chatty_commander.web.routes.agents as a
print("is llm_manager None?", a._llm_manager is None)
print("what is it?", a._llm_manager)

bp = a.parse_blueprint_from_text("My helpful agent who summarizes docs")
print("blueprint", bp)
