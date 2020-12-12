

from traits.api import Float, Instance, Enum, Array

from traitsui.api import View, Item, VGroup, HGroup

from tvtk.api import tvtk
from tvtk.pyface.scene_model import SceneModel
from tvtk.pyface.scene_editor import SceneEditor

from raytrace.results import Result
from raytrace.fields import EFieldPlane
from raytrace.custom_sources import NumpyImageSource


class IntensitySurface(Result):
    field_probe = Instance(EFieldPlane)
    
    display = Enum("Intensity", "E_x", "E_y", "E_z")
    
    intensity_data = Array()
    
    scale = Float(1.0)
    
    #scene = Instance(SceneModel, (), {'background':(0,0,0)}, transient=True)
    scene = Instance(SceneModel, transient=True)
    
    _data_source = Instance(NumpyImageSource, ())
    _warp = Instance(tvtk.WarpScalar)
    
    traits_view = View(VGroup(
                        HGroup(
                            Item("display", show_label=False),
                            Item("scale", show_label=False)
                            ),
                        Item("scene", editor=SceneEditor(), show_label=False)
                        ))
    
    def _intensity_data_changed(self, data):
        self._data_source.image_data = data
        
    def _scale_changed(self, value):
        w = self._warp
        if w is not None:
            w.scale_factor = value
            w.modified()
        
    def _scene_default(self):
        scene = SceneModel(background=(0,0,0))
        
        src = self._data_source
        src.update()
        
        geom = tvtk.ImageDataGeometryFilter(input_connection=src.output_port)
        
        warp = tvtk.WarpScalar(input_connection=geom.output_port,
                               scale_factor=self.scale)
        self._warp = warp
        
        mapper = tvtk.PolyDataMapper(input_connection=warp.output_port)
        #mapper.scalar_range = (-2.,2.)
        
        act = tvtk.Actor(mapper=mapper)
        scene.add_actor(act)
        return scene
    
    def calc_intensity(self, e_field):
        E = e_field
        mode = self.display
        if mode=="Intensity":
            U = (E.real**2).sum(axis=-1) + (E.imag**2).sum(axis=-1)
        else:
            idx = {"E_x":0, "E_y":1, "E_z":2}[mode]
            U = E[:,:,idx]
        self.intensity_data = U
        return U
    
    def _display_changed(self):
        self.on_field_changed(self.field_probe.E_field)
    
    def calc_result(self, model):
        pass
        #self.calc_intensity(self.field_probe.E_field)
    
    def _field_probe_changed(self, old, new):
        if old is not None:
            old.on_trait_change(self.on_field_changed, "E_field", remove=True)
        new.on_trait_change(self.on_field_changed, "E_field")
        
    def on_field_changed(self, e_field):
        intensity_image = self.calc_intensity(e_field)
        
            
            
if __name__=="__main__":
    import numpy
    vm = IntensitySurface()
    
    _x = numpy.linspace(-1,1,50)
    _y = numpy.linspace(-1,1,50)
    x,y = numpy.meshgrid(_x,_y)
    
    z = numpy.exp(-(x**2 + y**2)/(0.5**2))
    
    vm.intensity_data = z
    
    vm.configure_traits()