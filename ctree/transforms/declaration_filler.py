import ast
import ctree.c.nodes as C
import ctypes as ct


class DeclarationFiller(ast.NodeTransformer):
    def __init__(self):
        self.__environments = [{}]

    def _lookup(self, key):
        """
        :param key:
        :return: Looks up the last value corresponding to key in
            self.__environments
        """
        if isinstance(key, C.SymbolRef):
            key = key.name
        value = sentinel = object()
        for environment in self.__environments:
            if key in environment:
                value = environment[key]
        if value is sentinel:
            raise KeyError('Did not find {} in environments'.format(repr(key)))
        return value

    def _has_key(self, key):
        try:
            self._lookup(key)
            return True
        except KeyError:
            return False

    def __add_entry(self, key, value):
        if isinstance(key, C.SymbolRef):
            key = key.name
        self.__environments[-1][key] = value

    def __add_environment(self):
        self.__environments.append({})

    def __pop_environment(self):
        return self.__environments.pop()

    def visit_FunctionDecl(self, node):
        # add current FunctionDecl's return type onto environments
        self.__add_entry(node.name, node.return_type)

        # new environment every time we enter a function
        self.__add_environment()

        for param in node.params:
            # binding types of parameters
            self.__add_entry(param.name, param.type)

        node.defn = [self.visit(i) for i in node.defn]
        self.__pop_environment()
        return node

    def visit_SymbolRef(self, node):

        if node.type is not None:
            self.__add_entry(node.name, node.type)
        return node

    def visit_FunctionCall(self, node):
        node.args = [self.visit(arg) for arg in node.args]
        if self._has_key(node.func):
            node.type = self._lookup(node.func)
        elif node.func.name in {'fmax', 'fmin'}:
            # Assume type of last argument for now
            # TODO: Is there something smarter we can do?
            if isinstance(node.args[0], C.SymbolRef):
                node.type = self._lookup(node.args[0])
            elif hasattr(node.args[0], 'get_type'):
                node.type = node.args[0].get_type(self)
            else:
                raise NotImplementedError(node.args[0])
        return node

    def visit_BinaryOp(self, node):
        if isinstance(node.op, C.Op.Assign):
            node.left = self.visit(node.left)
            if isinstance(node.left, C.BinaryOp):
                return node
            node.right = self.visit(node.right)
            name = node.left
            value = node.right
            if hasattr(name, 'type') and name.type is not None:
                return node
            if hasattr(name, 'name') and not self._has_key(name.name):
                # temporary variable types can be derived from the variables
                # that they represent
                if name.name.startswith('____temp__'):
                    stripped_name = name.name.lstrip('____temp__')
                    if self._has_key(stripped_name):
                        node.left.type = self._lookup(stripped_name)
                    elif hasattr(value, 'get_type'):
                        node.left.type = value.get_type(self)
                    elif isinstance(value, C.FunctionCall):
                        if self._has_key(value.func):
                            node.left.type = self._lookup(value.func)
                        elif hasattr(value, 'type'):
                            node.left.type = value.type
                elif hasattr(value, 'get_type'):
                    node.left.type = value.get_type()
                elif isinstance(value, C.String):
                    node.left.type = ct.c_char_p()
                elif isinstance(value, C.SymbolRef):
                    node.left.type = self._lookup(value.name)

                self.__add_entry(node.left.name, node.left.type)
        return node
