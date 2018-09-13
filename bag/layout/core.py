# -*- coding: utf-8 -*-

"""This module defines the base template class.
"""

from typing import TYPE_CHECKING, List, Tuple, Optional, Any

import abc
import math
from itertools import chain

import bag
import bag.io
from .util import BBox
from bag.util.search import BinaryIterator

# try to import cython classes
from pybag.layout import PyTech

if TYPE_CHECKING:
    from pybag.layout import PyLayInstance


class TechInfo(object, metaclass=abc.ABCMeta):
    """A base class that create vias.

    This class provides the API for making vias.  Each process should subclass this class and
    implement the make_via method.

    Parameters
    ----------
    res : float
        the grid resolution of this technology.
    layout_unit : float
        the layout unit, in meters.
    via_tech : string
        the via technology library name.  This is usually the PDK library name.
    process_params : dict[str, any]
        process specific parameters.

    Attributes
    ----------
    tech_params : dict[str, any]
        technology specific parameters.
    """

    def __init__(self, res, layout_unit, via_tech, process_params):
        self._resolution = res
        self._layout_unit = layout_unit
        self._via_tech = via_tech
        self.tech_params = process_params
        self.pybag_tech = PyTech(process_params['pybag'], bag.io.get_encoding())

    @abc.abstractmethod
    def get_well_layers(self, sub_type):
        # type: (str) -> List[Tuple[str, str]]
        """Returns a list of well layers associated with the given substrate type."""
        return []

    @abc.abstractmethod
    def get_implant_layers(self, mos_type, res_type=None):
        # type: (str, Optional[str]) -> List[Tuple[str, str]]
        """Returns a list of implant layers associated with the given device type.

        Parameters
        ----------
        mos_type : str
            one of 'nch', 'pch', 'ntap', or 'ptap'
        res_type : Optional[str]
            If given, the return layers will be for the substrate of the given resistor type.

        Returns
        -------
        imp_list : List[Tuple[str, str]]
            list of implant layers.
        """
        return []

    @abc.abstractmethod
    def get_threshold_layers(self, mos_type, threshold, res_type=None):
        # type: (str, str, Optional[str]) -> List[Tuple[str, str]]
        """Returns a list of threshold layers."""
        return []

    @abc.abstractmethod
    def get_exclude_layer(self, layer_id):
        # type: (int) -> Tuple[str, str]
        """Returns the metal exclude layer"""
        return '', ''

    @abc.abstractmethod
    def get_dnw_margin_unit(self, dnw_mode):
        # type: (str) -> int
        """Returns the required DNW margin given the DNW mode.

        Parameters
        ----------
        dnw_mode : str
            the DNW mode string.

        Returns
        -------
        dnw_margin : int
            the DNW margin in resolution units.
        """
        return 0

    @abc.abstractmethod
    def get_dnw_layers(self):
        # type: () -> List[Tuple[str, str]]
        """Returns a list of layers that defines DNW.

        Returns
        -------
        lay_list : List[Tuple[str, str]]
            list of DNW layers.
        """
        return []

    @abc.abstractmethod
    def get_res_metal_layers(self, layer_id):
        # type: (int) -> List[Tuple[str, str]]
        """Returns a list of layers associated with the given metal resistor.

        Parameters
        ----------
        layer_id : int
            the metal layer ID.

        Returns
        -------
        res_list : List[Tuple[str, str]]
            list of resistor layers.
        """
        return []

    @abc.abstractmethod
    def add_cell_boundary(self, template, box):
        """Adds a cell boundary object to the given template.
        
        This is usually the PR boundary.
        
        Parameters
        ----------
        template : TemplateBase
            the template to draw the cell boundary in.
        box : BBox
            the cell boundary bounding box.
        """
        pass

    @abc.abstractmethod
    def draw_device_blockage(self, template):
        """Draw device blockage layers on the given template.

        Parameters
        ----------
        template : TemplateBase
            the template to draw the device block layers on
        """
        pass

    @abc.abstractmethod
    def get_via_drc_info(self, vname, vtype, mtype, mw_unit, is_bot):
        """Return data structures used to identify VIA DRC rules.

        Parameters
        ----------
        vname : string
            the via type name.
        vtype : string
            the via type, square/hrect/vrect/etc.
        mtype : string
            name of the metal layer via is connecting.  Can be either top or bottom.
        mw_unit : int
            width of the metal, in resolution units.
        is_bot : bool
            True if the given metal is the bottom metal.

        Returns
        -------
        sp : Tuple[int, int]
            horizontal/vertical space between adjacent vias, in resolution units.
        sp3 : Tuple[int, int] or None
            horizontal/vertical space between adjacent vias if the via has 3 or more neighbors.
            None if no constraint.
        dim : Tuple[int, int]
            the via width/height in resolution units.
        enc : List[Tuple[int, int]]
            a list of valid horizontal/vertical enclosure of the via on the given metal
            layer, in resolution units.
        arr_enc : List[Tuple[int, int]] or None
            a list of valid horizontal/vertical enclosure of the via on the given metal
            layer if this is a "via array", in layout units.
            None if no constraint.
        arr_test : callable or None
            a function that accepts two inputs, the number of via rows and number of via
            columns, and returns True if those numbers describe a "via array".
            None if no constraint.
        """
        return (0, 0), (0, 0), (0, 0), [(0, 0)], None, None

    @abc.abstractmethod
    def get_min_space(self, layer_type, width, unit_mode=False, same_color=False):
        """Returns the minimum spacing needed around a wire on the given layer with the given width.

        Parameters
        ----------
        layer_type : str
            the wiring layer type.
        width : Union[float, int]
            the width of the wire, in layout units.
        unit_mode : bool
            True if dimension are given/returned in resolution units.
        same_color : bool
            True to use same-color spacing.

        Returns
        -------
        sp : Union[float, int]
            the minimum spacing needed.
        """
        return 0.0

    @abc.abstractmethod
    def get_min_line_end_space(self, layer_type, width, unit_mode=False):
        """Returns the minimum line-end spacing of a wire with given width.

        Parameters
        ----------
        layer_type : str
            the wiring layer type.
        width : Union[float, int]
            the width of the wire, in layout units.
        unit_mode : bool
            True if dimension are given/returned in resolution units.

        Returns
        -------
        sp : Union[float, int]
            the minimum line-end space.
        """
        return 0.0

    @abc.abstractmethod
    def get_min_length(self, layer_type, width):
        # type: (str, float) -> float
        """Returns the minimum length of a wire on the given layer with the given width.

        Parameters
        ----------
        layer_type : str
            the wiring layer type.
        width : float
            the width of the wire, in layout units.

        Returns
        -------
        min_length : float
            the minimum length.
        """
        return 0.0

    @abc.abstractmethod
    def get_layer_id(self, layer_name):
        """Return the layer id for the given layer name.

        Parameters
        ----------
        layer_name : string
            the layer name.

        Returns
        -------
        layer_id : int
            the layer ID.
        """
        return 0

    @abc.abstractmethod
    def get_layer_name(self, layer_id):
        """Return the layer name(s) for the given routing grid layer ID.

        Parameters
        ----------
        layer_id : int
            the routing grid layer ID.

        Returns
        -------
        name : string or Tuple[string]
            name of the layer.  Returns a tuple of names if this is a double
            patterning layer.
        """
        return ''

    @abc.abstractmethod
    def get_layer_type(self, layer_name):
        """Returns the metal type of the given wiring layer.

        Parameters
        ----------
        layer_name : str
            the wiring layer name.

        Returns
        -------
        metal_type : string
            the metal layer type.
        """
        return ''

    @abc.abstractmethod
    def get_via_name(self, bot_layer_id):
        """Returns the via type name of the given via.

        Parameters
        ----------
        bot_layer_id : int
            the via bottom layer ID

        Returns
        -------
        name : string
            the via type name.
        """
        return ''

    @abc.abstractmethod
    def get_metal_em_specs(self, layer_name, w, l=-1, vertical=False, **kwargs):
        """Returns a tuple of EM current/resistance specs of the given wire.

        Parameters
        ----------
        layer_name : str
            the metal layer name.
        w : float
            the width of the metal in layout units (dimension perpendicular to current flow).
        l : float
            the length of the metal in layout units (dimension parallel to current flow).
            If negative, disable length enhancement.
        vertical : bool
            True to compute vertical current.
        **kwargs :
            optional EM specs parameters.

        Returns
        -------
        idc : float
            maximum DC current, in Amperes.
        iac_rms : float
            maximum AC RMS current, in Amperes.
        iac_peak : float
            maximum AC peak current, in Amperes.
        """
        return float('inf'), float('inf'), float('inf')

    @abc.abstractmethod
    def get_via_em_specs(self, via_name,  # type: str
                         bm_layer,  # type: str
                         tm_layer,  # type: str
                         via_type='square',  # type: str
                         bm_dim=(-1, -1),  # type: Tuple[float, float]
                         tm_dim=(-1, -1),  # type: Tuple[float, float]
                         array=False,  # type: bool
                         **kwargs):
        # type: (...) -> Tuple[float ,float, float]
        """Returns a tuple of EM current/resistance specs of the given via.

        Parameters
        ----------
        via_name : str
            the via type name.
        bm_layer : str
            the bottom layer name.
        tm_layer : str
            the top layer name.
        via_type : str
            the via type, square/vrect/hrect/etc.
        bm_dim : Tuple[float, float]
            bottom layer metal width/length in layout units.  If negative,
            disable length/width enhancement.
        tm_dim : Tuple[float, float]
            top layer metal width/length in layout units.  If negative,
            disable length/width enhancement.
        array : bool
            True if this via is in a via array.
        **kwargs :
            optional EM specs parameters.

        Returns
        -------
        idc : float
            maximum DC current per via, in Amperes.
        iac_rms : float
            maximum AC RMS current per via, in Amperes.
        iac_peak : float
            maximum AC peak current per via, in Amperes.
        """
        return float('inf'), float('inf'), float('inf')

    @abc.abstractmethod
    def get_res_rsquare(self, res_type):
        """Returns R-square for the given resistor type.

        This is used to do some approximate resistor dimension calculation.

        Parameters
        ----------
        res_type : string
            the resistor type.

        Returns
        -------
        rsquare : float
            resistance in Ohms per unit square of the given resistor type.
        """
        return 0.0

    @abc.abstractmethod
    def get_res_width_bounds(self, res_type):
        """Returns the maximum and minimum resistor width for the given resistor type.

        Parameters
        ----------
        res_type : string
            the resistor type.

        Returns
        -------
        wmin : float
            minimum resistor width, in layout units.
        wmax : float
            maximum resistor width, in layout units.
        """
        return 0.0, 0.0

    @abc.abstractmethod
    def get_res_length_bounds(self, res_type):
        """Returns the maximum and minimum resistor length for the given resistor type.

        Parameters
        ----------
        res_type : string
            the resistor type.

        Returns
        -------
        lmin : float
            minimum resistor length, in layout units.
        lmax : float
            maximum resistor length, in layout units.
        """
        return 0.0, 0.0

    @abc.abstractmethod
    def get_res_min_nsquare(self, res_type):
        """Returns the minimum allowable number of squares for the given resistor type.

        Parameters
        ----------
        res_type : string
            the resistor type.

        Returns
        -------
        nsq_min : flaot
            minimum number of squares needed.
        """
        return 1.0

    @abc.abstractmethod
    def get_res_em_specs(self, res_type, w, l=-1, **kwargs):
        # type: (str, float, float, Any) -> Tuple[float, float, float]
        """Returns a tuple of EM current/resistance specs of the given resistor.

        Parameters
        ----------
        res_type : string
            the resistor type string.
        w : float
            the width of the metal in layout units (dimension perpendicular to current flow).
        l : float
            the length of the metal in layout units (dimension parallel to current flow).
            If negative, disable length enhancement.
        **kwargs :
            optional EM specs parameters.

        Returns
        -------
        idc : float
            maximum DC current, in Amperes.
        iac_rms : float
            maximum AC RMS current, in Amperes.
        iac_peak : float
            maximum AC peak current, in Amperes.
        """
        return float('inf'), float('inf'), float('inf')

    @property
    def via_tech_name(self):
        """Returns the via technology library name."""
        return self._via_tech

    @property
    def pin_purpose(self):
        """Returns the layout pin purpose name."""
        return 'pin'

    @property
    def resolution(self):
        """Returns the grid resolution."""
        return self._resolution

    @property
    def layout_unit(self):
        """Returns the layout unit length, in meters."""
        return self._layout_unit

    def merge_well(self,
                   template,  # type: 'TemplateBase'
                   inst_list,  # type: List[PyLayInstance]
                   sub_type,  # type: str
                   threshold=None,  # type: Optional[str]
                   res_type=None,  # type: Optional[str]
                   merge_imp=False,  # type: bool
                   ):
        # type: (...) -> None
        """Merge the well of the given instances together."""

        if threshold is not None:
            lay_iter = chain(self.get_well_layers(sub_type),
                             self.get_threshold_layers(sub_type, threshold, res_type=res_type))
        else:
            lay_iter = self.get_well_layers(sub_type)
        if merge_imp:
            lay_iter = chain(lay_iter, self.get_implant_layers(sub_type, res_type=res_type))

        for lay in lay_iter:
            tot_box = BBox.get_invalid_bbox()
            for inst in inst_list:
                cur_box = inst.master.get_rect_bbox(lay)
                tot_box = tot_box.merge(inst.translate_master_box(cur_box))
            if tot_box.is_physical():
                template.add_rect(lay, tot_box)

    def use_flip_parity(self):
        # type: () -> bool
        """Returns True if flip_parity dictionary is needed in this technology."""
        return True

    def finalize_template(self, template):
        """Perform any operations necessary on the given layout template before finalizing it.

        By default, nothing is done.

        Parameters
        ----------
        template : TemplateBase
            the template object.
        """
        pass

    def get_res_info(self, res_type, w, l, **kwargs):
        """Returns a dictionary containing EM information of the given resistor.

        Parameters
        ----------
        res_type : string or (string, string)
            the resistor type.
        w : float
            the resistor width in layout units (dimension perpendicular to current flow).
        l : float
            the resistor length in layout units (dimension parallel to current flow).
        **kwargs :
            optional parameters for EM rule calculations, such as nominal temperature,
            AC rms delta-T, etc.

        Returns
        -------
        info : dict[string, any]
            A dictionary of wire information.  Should have the following:

            resistance : float
                The resistance, in Ohms.
            idc : float
                The maximum allowable DC current, in Amperes.
            iac_rms : float
                The maximum allowable AC RMS current, in Amperes.
            iac_peak : float
                The maximum allowable AC peak current, in Amperes.
        """
        rsq = self.get_res_rsquare(res_type)
        res = l / w * rsq
        idc, irms, ipeak = self.get_res_em_specs(res_type, w, l=l, **kwargs)

        return dict(
            resistance=res,
            idc=idc,
            iac_rms=irms,
            iac_peak=ipeak,
        )

    def get_via_types(self, bmtype, tmtype):
        return [('square', 1), ('vrect', 2), ('hrect', 2)]

    def get_best_via_array(self, vname, bmtype, tmtype, bot_dir, top_dir, w, h, extend):
        """Maximize the number of vias in the given area.

        Parameters
        ----------
        vname : str
            the via type name.
        bmtype : str
            the bottom metal type name.
        tmtype : str
            the top metal type name.
        bot_dir : str
            the bottom wire direction.  Either 'x' or 'y'.
        top_dir : str
            the top wire direction.  Either 'x' or 'y'.
        w : int
            width of the via array bounding box.
        h : int
            height of the via array bounding box.
        extend : bool
            True if via can extend beyond bounding box.

        Returns
        -------
        best_nxy : Tuple[int, int]
            optimal number of vias per row/column.
        best_mdim_list : List[Tuple[int, int]]
            a list of bottom/top layer width/height, in resolution units.
        vtype : str
            the via type to draw, square/hrect/vrect/etc.
        vdim : Tuple[int, int]
            the via width/height, in resolution units.
        via_space : Tuple[int, int]
            the via horizontal/vertical spacing, in resolution units.
        via_arr_dim : Tuple[int, int]
            the via array width/height, in resolution units.
        """
        if bot_dir == 'x':
            bb, be = h, w
        else:
            bb, be = w, h
        if top_dir == 'x':
            tb, te = h, w
        else:
            tb, te = w, h

        best_num = None
        best_nxy = [-1, -1]
        best_mdim_list = None
        best_type = None
        best_vdim = None
        best_sp = None
        best_adim = None
        via_type_list = self.get_via_types(bmtype, tmtype)
        for vtype, weight in via_type_list:
            try:
                # get space and enclosure rules for top and bottom layer
                bot_drc_info = self.get_via_drc_info(vname, vtype, bmtype, bb, True)
                top_drc_info = self.get_via_drc_info(vname, vtype, tmtype, tb, False)
                sp, sp2_list, sp3_list, dim, encb, arr_encb, arr_testb = bot_drc_info
                _, _, _, _, enct, arr_enct, arr_testt = top_drc_info
                # print _get_via_params(vname, vtype, bmtype, bw)
                # print _get_via_params(vname, vtype, tmtype, tw)
            except ValueError:
                continue

            # compute maximum possible nx and ny
            if sp2_list is None:
                sp2_list = [sp]
            if sp3_list is None:
                sp3_list = sp2_list
            spx_min, spy_min = sp
            for high_sp_list in (sp2_list, sp3_list):
                for high_spx, high_spy in high_sp_list:
                    spx_min = min(spx_min, high_spx)
                    spy_min = min(spy_min, high_spy)

            nx_max = (w + spx_min) // (dim[0] + spx_min)
            ny_max = (h + spy_min) // (dim[1] + spy_min)

            # print nx_max, ny_max, dim, w, h, spx_min, spy_min

            # generate list of possible nx/ny configuration
            nxy_list = [(a * b, a, b) for a in range(1, nx_max + 1) for b in range(1, ny_max + 1)]
            nxy_list = sorted(nxy_list, reverse=True)

            # find best nx/ny configuration
            opt_nxy = None
            opt_mdim_list = None
            opt_adim = None
            opt_sp = None
            for num, nx, ny in nxy_list:
                # check if we need to use sp3
                if nx == 2 and ny == 2:
                    sp_combo = sp2_list
                elif nx > 1 and ny > 1:
                    sp_combo = sp3_list
                else:
                    sp_combo = [sp]

                for spx, spy in sp_combo:
                    # get via array bounding box
                    w_arr = nx * (spx + dim[0]) - spx
                    h_arr = ny * (spy + dim[1]) - spy
                    mdim_list = [None, None]
                    # check at least one enclosure rule is satisfied for both top and bottom layer
                    for idx, (mdir, tot_enc_list, arr_enc, arr_test) in \
                            enumerate([(bot_dir, encb, arr_encb, arr_testb),
                                       (top_dir, enct, arr_enct, arr_testt)]):
                        # check if array enclosure rule applies
                        if arr_test is not None and arr_test(ny, nx):
                            tot_enc_list = tot_enc_list + arr_enc

                        if mdir == 'y':
                            enc_idx = 0
                            enc_dim = w_arr
                            ext_dim = h_arr
                            dim_lim = w
                            max_ext_dim = h
                        else:
                            enc_idx = 1
                            enc_dim = h_arr
                            ext_dim = w_arr
                            dim_lim = h
                            max_ext_dim = w

                        min_ext_dim = None
                        for enc in tot_enc_list:
                            cur_ext_dim = ext_dim + 2 * enc[1 - enc_idx]
                            if enc[enc_idx] * 2 + enc_dim <= dim_lim and \
                                    (extend or cur_ext_dim <= max_ext_dim):
                                # enclosure rule passed.  Find minimum other dimension
                                if min_ext_dim is None or min_ext_dim > cur_ext_dim:
                                    min_ext_dim = cur_ext_dim

                        if min_ext_dim is None:
                            # all enclosure rule failed.  Exit.
                            break
                        else:
                            # record metal dimension.
                            min_ext_dim = max(min_ext_dim, max_ext_dim)
                            mdim_list[idx] = [min_ext_dim, min_ext_dim]
                            mdim_list[idx][enc_idx] = dim_lim

                    if mdim_list[0] is not None and mdim_list[1] is not None:
                        # passed
                        opt_mdim_list = mdim_list
                        opt_nxy = (nx, ny)
                        opt_adim = (w_arr, h_arr)
                        opt_sp = (spx, spy)
                        break

                if opt_nxy is not None:
                    break

            if opt_nxy is not None:
                opt_num = weight * opt_nxy[0] * opt_nxy[1]
                if (best_num is None or opt_num > best_num or
                        (opt_num == best_num and self._via_better(opt_mdim_list, best_mdim_list))):
                    best_num = opt_num
                    best_nxy = opt_nxy
                    best_mdim_list = opt_mdim_list
                    best_type = vtype
                    best_vdim = dim
                    best_sp = opt_sp
                    best_adim = opt_adim

        if best_num is None:
            return None
        return best_nxy, best_mdim_list, best_type, best_vdim, best_sp, best_adim

    def _via_better(self, mdim_list1, mdim_list2):
        """Returns true if the via in mdim_list1 has smaller area compared with via in mdim_list2"""
        res = self._resolution
        better = False
        for mdim1, mdim2 in zip(mdim_list1, mdim_list2):
            area1 = int(round(mdim1[0] / res)) * int(round(mdim1[1] / res))
            area2 = int(round(mdim2[0] / res)) * int(round(mdim2[1] / res))
            if area1 < area2:
                better = True
            elif area1 > area2:
                return False
        return better

    # noinspection PyMethodMayBeStatic
    def get_via_id(self, bot_layer, top_layer):
        """Returns the via ID string given bottom and top layer name.

        Defaults to "<bot_layer>_<top_layer>"

        Parameters
        ----------
        bot_layer : string
            the bottom layer name.
        top_layer : string
            the top layer name.

        Returns
        -------
        via_id : string
            the via ID string.
        """
        return '%s_%s' % (top_layer, bot_layer)

    def get_via_info(self, bbox, bot_layer, top_layer, bot_dir, bot_len=-1, top_len=-1,
                     extend=True, top_dir=None, **kwargs):
        """Create a via on the routing grid given the bounding box.

        Parameters
        ----------
        bbox : bag.layout.util.BBox
            the bounding box of the via.
        bot_layer : Union[str, Tuple[str, str]]
            the bottom layer name, or a tuple of layer name and purpose name.
            If purpose name not given, defaults to 'drawing'.
        top_layer : Union[str, Tuple[str, str]]
            the top layer name, or a tuple of layer name and purpose name.
            If purpose name not given, defaults to 'drawing'.
        bot_dir : str
            the bottom layer extension direction.  Either 'x' or 'y'
        bot_len : float
            length of bottom wire connected to this Via, in layout units.
            Used for length enhancement EM calculation.
        top_len : float
            length of top wire connected to this Via, in layout units.
            Used for length enhancement EM calculation.
        extend : bool
            True if via extension can be drawn outside of bounding box.
        top_dir : Optional[str]
            top layer extension direction.  Can force to extend in same direction as bottom.
        **kwargs :
            optional parameters for EM rule calculations, such as nominal temperature,
            AC rms delta-T, etc.

        Returns
        -------
        info : dict[string, any]
            A dictionary of via information, or None if no solution.  Should have the following:

            resistance : float
                The total via array resistance, in Ohms.
            idc : float
                The total via array maximum allowable DC current, in Amperes.
            iac_rms : float
                The total via array maximum allowable AC RMS current, in Amperes.
            iac_peak : float
                The total via array maximum allowable AC peak current, in Amperes.
            params : dict[str, any]
                A dictionary of via parameters.
            top_box : bag.layout.util.BBox
                the top via layer bounding box, including extensions.
            bot_box : bag.layout.util.BBox
                the bottom via layer bounding box, including extensions.

        """
        # remove purpose
        if isinstance(bot_layer, tuple):
            bot_layer = bot_layer[0]
        if isinstance(top_layer, tuple):
            top_layer = top_layer[0]
        bot_layer = bag.io.fix_string(bot_layer)
        top_layer = bag.io.fix_string(top_layer)

        bot_id = self.get_layer_id(bot_layer)
        bmtype = self.get_layer_type(bot_layer)
        tmtype = self.get_layer_type(top_layer)
        vname = self.get_via_name(bot_id)

        if not top_dir:
            top_dir = 'x' if bot_dir == 'y' else 'y'

        via_result = self.get_best_via_array(vname, bmtype, tmtype, bot_dir, top_dir,
                                             bbox.w, bbox.h, extend)
        if via_result is None:
            # no solution found
            return None

        (nx, ny), mdim_list, vtype, vdim, (spx, spy), (warr_norm, harr_norm) = via_result

        res = self.resolution
        xc_norm = bbox.xc_unit
        yc_norm = bbox.yc_unit

        wbot_norm = mdim_list[0][0]
        hbot_norm = mdim_list[0][1]
        wtop_norm = mdim_list[1][0]
        htop_norm = mdim_list[1][1]

        # OpenAccess Via can't handle even + odd enclosure, so we truncate.
        enc1_x = (wbot_norm - warr_norm) // 2
        enc1_y = (hbot_norm - harr_norm) // 2
        enc2_x = (wtop_norm - warr_norm) // 2
        enc2_y = (htop_norm - harr_norm) // 2

        # compute EM rule dimensions
        if bot_dir == 'x':
            bw, tw = hbot_norm * res, wtop_norm * res
        else:
            bw, tw = wbot_norm * res, htop_norm * res

        bot_xl_norm = xc_norm - wbot_norm // 2
        bot_yb_norm = yc_norm - hbot_norm // 2
        top_xl_norm = xc_norm - wtop_norm // 2
        top_yb_norm = yc_norm - htop_norm // 2

        bot_box = BBox(bot_xl_norm, bot_yb_norm, bot_xl_norm + wbot_norm,
                       bot_yb_norm + hbot_norm, res, unit_mode=True)
        top_box = BBox(top_xl_norm, top_yb_norm, top_xl_norm + wtop_norm,
                       top_yb_norm + htop_norm, res, unit_mode=True)

        idc, irms, ipeak = self.get_via_em_specs(vname, bot_layer, top_layer, via_type=vtype,
                                                 bm_dim=(bw, bot_len), tm_dim=(tw, top_len),
                                                 array=nx > 1 or ny > 1, **kwargs)

        params = {'id': self.get_via_id(bot_layer, top_layer),
                  'loc': (xc_norm, yc_norm),
                  'orient': 'R0',
                  'num_rows': ny,
                  'num_cols': nx,
                  'sp_rows': spy,
                  'sp_cols': spx,
                  # increase left/bottom enclusion if off-center.
                  'enc1': [enc1_x, enc1_x, enc1_y, enc1_y],
                  'enc2': [enc2_x, enc2_x, enc2_y, enc2_y],
                  'cut_width': vdim[0],
                  'cut_height': vdim[1],
                  }

        ntot = nx * ny
        return dict(
            resistance=0.0,
            idc=idc * ntot,
            iac_rms=irms * ntot,
            iac_peak=ipeak * ntot,
            params=params,
            top_box=top_box,
            bot_box=bot_box,
        )

    def design_resistor(self, res_type, res_targ, idc=0.0, iac_rms=0.0,
                        iac_peak=0.0, num_even=True, **kwargs):
        """Finds the optimal resistor dimension that meets the given specs.

        Assumes resistor length does not effect EM specs.

        Parameters
        ----------
        res_type : string
            the resistor type.
        res_targ : float
            target resistor, in Ohms.
        idc : float
            maximum DC current spec, in Amperes.
        iac_rms : float
            maximum AC RMS current spec, in Amperes.
        iac_peak : float
            maximum AC peak current spec, in Amperes.
        num_even : int
            True to return even number of resistors.
        **kwargs :
            optional EM spec calculation parameters.

        Returns
        -------
        num_par : int
            number of resistors needed in parallel.
        num_ser : int
            number of resistors needed in series.
        w : float
            width of a unit resistor, in meters.
        l : float
            length of a unit resistor, in meters.
        """
        resolution = self.resolution
        rsq = self.get_res_rsquare(res_type)
        wmin, wmax = self.get_res_width_bounds(res_type)
        lmin, lmax = self.get_res_length_bounds(res_type)
        min_nsq = self.get_res_min_nsquare(res_type)

        wmin_unit = int(round(wmin / resolution))
        wmax_unit = int(round(wmax / resolution))
        lmin_unit = int(round(lmin / resolution))
        lmax_unit = int(round(lmax / resolution))
        # make sure width is always even
        wmin_unit = -2 * (-wmin_unit // 2)
        wmax_unit = 2 * (wmax_unit // 2)

        # step 1: find number of parallel resistors and minimum resistor width.
        if num_even:
            npar_iter = BinaryIterator(2, None, step=2)
        else:
            npar_iter = BinaryIterator(1, None, step=1)
        while npar_iter.has_next():
            npar = npar_iter.get_next()
            res_targ_par = res_targ * npar
            idc_par = idc / npar
            iac_rms_par = iac_rms / npar
            iac_peak_par = iac_peak / npar
            res_idc, res_irms, res_ipeak = self.get_res_em_specs(res_type, wmax, **kwargs)
            if (0.0 < res_idc < idc_par or 0.0 < res_irms < iac_rms_par or
                    0.0 < res_ipeak < iac_peak_par):
                npar_iter.up()
            else:
                # This could potentially work, find width solution
                w_iter = BinaryIterator(wmin_unit, wmax_unit + 1, step=2)
                while w_iter.has_next():
                    wcur_unit = w_iter.get_next()
                    lcur_unit = int(math.ceil(res_targ_par / rsq * wcur_unit))
                    if lcur_unit < max(lmin_unit, int(math.ceil(min_nsq * wcur_unit))):
                        w_iter.down()
                    else:
                        tmp = self.get_res_em_specs(res_type, wcur_unit * resolution,
                                                    l=lcur_unit * resolution, **kwargs)
                        res_idc, res_irms, res_ipeak = tmp
                        if (0.0 < res_idc < idc_par or 0.0 < res_irms < iac_rms_par or
                                0.0 < res_ipeak < iac_peak_par):
                            w_iter.up()
                        else:
                            w_iter.save_info((wcur_unit, lcur_unit))
                            w_iter.down()

                w_info = w_iter.get_last_save_info()
                if w_info is None:
                    # no solution; we need more parallel resistors
                    npar_iter.up()
                else:
                    # solution!
                    npar_iter.save_info((npar, w_info[0], w_info[1]))
                    npar_iter.down()

        # step 3: fix maximum length violation by having resistor in series.
        num_par, wopt_unit, lopt_unit = npar_iter.get_last_save_info()
        wopt = wopt_unit * resolution
        if lopt_unit > lmax_unit:
            num_ser = -(-lopt_unit // lmax_unit)
            lopt = round(lopt_unit / num_ser / resolution) * resolution
        else:
            num_ser = 1
            lopt = lopt_unit * resolution

        # step 4: return answer
        return num_par, num_ser, wopt * self.layout_unit, lopt * self.layout_unit


class DummyTechInfo(TechInfo):
    """A dummy TechInfo class.

    Parameters
    ----------
    tech_params : dict[str, any]
        technology parameters dictionary.
    """

    def __init__(self, tech_params):
        TechInfo.__init__(self, 0.001, 1e-6, '', tech_params)

    def get_well_layers(self, sub_type):
        return []

    def get_implant_layers(self, mos_type, res_type=None):
        return []

    def get_threshold_layers(self, mos_type, threshold, res_type=None):
        return []

    def get_dnw_layers(self):
        # type: () -> List[Tuple[str, str]]
        return []

    def get_exclude_layer(self, layer_id):
        # type: (int) -> Tuple[str, str]
        """Returns the metal exclude layer"""
        return '', ''

    def get_dnw_margin_unit(self, dnw_mode):
        # type: (str) -> int
        return 0

    def get_res_metal_layers(self, layer_id):
        # type: (int) -> List[Tuple[str, str]]
        return []

    def add_cell_boundary(self, template, box):
        pass

    def draw_device_blockage(self, template):
        pass

    def get_via_drc_info(self, vname, vtype, mtype, mw_unit, is_bot):
        return (0, 0), [(0, 0)], [(0, 0)], (0, 0), [(0, 0)], None, None

    def get_min_space(self, layer_type, width, unit_mode=False, same_color=False):
        return 0

    def get_min_line_end_space(self, layer_type, width, unit_mode=False):
        return 0

    def get_min_length(self, layer_type, width):
        return 0.0

    def get_layer_id(self, layer_name):
        return -1

    def get_layer_name(self, layer_id):
        return ''

    def get_layer_type(self, layer_name):
        return ''

    def get_via_name(self, bot_layer_id):
        return ''

    def get_metal_em_specs(self, layer_name, w, l=-1, vertical=False, **kwargs):
        return float('inf'), float('inf'), float('inf')

    def get_via_em_specs(self, via_name, bm_layer, tm_layer, via_type='square',
                         bm_dim=(-1, -1), tm_dim=(-1, -1), array=False, **kwargs):
        return float('inf'), float('inf'), float('inf')

    def get_res_rsquare(self, res_type):
        return 0.0

    def get_res_width_bounds(self, res_type):
        return 0.0, 0.0

    def get_res_length_bounds(self, res_type):
        return 0.0, 0.0

    def get_res_min_nsquare(self, res_type):
        return 1.0

    def get_res_em_specs(self, res_type, w, l=-1, **kwargs):
        return float('inf'), float('inf'), float('inf')
