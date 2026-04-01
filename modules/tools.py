# Tool Repository Code...
# Implementing the Tool Repo

class ToolRepo:
    def __init__(self):
        self.tools = {}

    def add_tool(self, name, tool):
        self.tools[name] = tool

    def get_tool(self, name):
        return self.tools.get(name, None)
