import claripy
import typing

from angr.storage.memory_object import SimMemoryObject

class CooperationBase:
    """
    Any given subclass of this class which is not a subclass of MemoryMixin should have the property that any subclass
    it which *is* a subclass of MemoryMixin should all work with the same datatypes
    """
    @classmethod
    def _compose_objects(cls, objects, size, endness, **kwargs):
        """
        Provide this a list of the result of several load calls, and it will compose them into a single result.
        """
        pass

    @classmethod
    def _decompose_objects(cls, addr, data, endness, **kwargs):
        """
        A bidirectional generator. No idea if this is overengineered. Usage is that you send it a size to use
        and it yields an object to store for the next n bytes.
        """
        pass

    @classmethod
    def _zero_objects(self, cls, addr, size, **kwargs):
        """
        Like decompose objects, but with a size to zero-fill instead of explicit data
        """
        pass

class MemoryObjectMixin(CooperationBase):
    """
    Uses SimMemoryObjects in region storage.
    With this, load will return a list of tuple (address, MO) and store will take a MO.
    """
    @classmethod
    def _compose_objects(cls, objects: typing.List[typing.List[typing.Tuple[int, SimMemoryObject]]], size, endness=None, **kwargs):
        c_objects = []
        for objlist in objects:
            for element in objlist:
                if not c_objects or element[1] is not c_objects[-1][1]:
                    c_objects.append(element)

        elements = [o.bytes_at(
                a,
                c_objects[i+1][0] - a if i != len(c_objects)-1 else c_objects[0][0] + size - a,
                endness=endness)
            for i, (a, o) in enumerate(c_objects)]
        if endness == 'Iend_LE':
            elements = reversed(elements)

        return claripy.Concat(*elements)

    @classmethod
    def _decompose_objects(cls, addr, data, endness, memory=None, **kwargs):
        # the generator model is definitely overengineered here but wouldn't be if we were working with raw BVs
        memory_object = SimMemoryObject(data, addr, endness, byte_width=memory.state.arch.byte_width if memory is not None else 8)
        size = yield
        while True:
            size = yield memory_object

    @classmethod
    def _zero_objects(cls, addr, size, memory=None, **kwargs):
        data = claripy.BVV(0, size*memory.state.arch.byte_width if memory is not None else 8)
        return cls._decompose_objects(addr, data, 'Iend_BE', memory=memory, **kwargs)
