#!/usr/bin/env python 
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
# Copyright (c) 2013-2019, NeXpy Development Team.
#
# Author: Paul Kienzle, Ray Osborn
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------

"""
The `nexus.tree` modules are designed to accomplish two goals:

    1. To provide convenient access to existing data contained in NeXus files.
    2. To enable new NeXus data to be created and manipulated interactively.

These goals are achieved by mapping hierarchical NeXus data structures directly
into python objects, which either represent NeXus groups or NeXus fields.
Entries in a group are referenced much like fields in a class are referenced in
python. The entire data hierarchy can be referenced at any time, whether the
NeXus data has been loaded in from an existing NeXus file or created dynamically
within the python session. This provides a natural scripting interface to NeXus 
data.

Example 1: Loading a NeXus file
-------------------------------
The following commands loads NeXus data from a file, displays (some of) the
contents as a tree, and then accesses individual data items

    >>> from nexusformat import nexus as nx
    >>> a=nx.load('sns/data/ARCS_7326.nxs')
    >>> print a.tree
    root:NXroot
      @HDF5_Version = 1.8.2
      @NeXus_version = 4.2.1
      @file_name = ARCS_7326.nxs
      @file_time = 2010-05-05T01:59:25-05:00
      entry:NXentry
        data:NXdata
          data = float32(631x461x4x825)
            @axes = rotation_angle:tilt_angle:sample_angle:time_of_flight
            @signal = 1
          rotation_angle = float32(632)
            @units = degree
          sample_angle = [ 210.  215.  220.  225.  230.]
            @units = degree
          tilt_angle = float32(462)
            @units = degree
          time_of_flight = float32(826)
            @units = microsecond
        run_number = 7326
        sample:NXsample
          pulse_time = 2854.94747365
            @units = microsecond
    .
    .
    .
    >>> a.entry.run_number
    NXfield(7326)

So the tree returned from :func:`load()` has an entry for each group, field and
attribute.  You can traverse the hierarchy using the names of the groups.  For
example, tree.entry.instrument.detector.distance is an example of a field
containing the distance to each pixel in the detector. Entries can also be
referenced by NXclass name, such as ``tree.NXentry[0].instrument``. Since there may
be multiple entries of the same NeXus class, the ``NXclass`` attribute returns a
(possibly empty) list.

The :func:`load()` and :func:`save()` functions are implemented using the class
`nexus.tree.NXFile`, a subclass of :class:`h5py.File`.

Example 2: Creating a NeXus file dynamically
--------------------------------------------
The second example shows how to create NeXus data dynamically and saves it to a
file. The data are first created as Numpy arrays

    >>> import numpy as np
    >>> x=y=np.linspace(0,2*np.pi,101)
    >>> X,Y=np.meshgrid(y,x)
    >>> z=np.sin(X)*np.sin(Y)

Then, a NeXus data group is created and the data inserted to produce a
NeXus-compliant structure that can be saved to a file

    >>> root=nx.NXroot(NXentry())
    >>> print root.tree
    root:NXroot
      entry:NXentry
    >>> root.entry.data=nx.NXdata(z,[x,y])

Additional metadata can be inserted before saving the data to a file.

    >>> root.entry.sample=nx.NXsample()
    >>> root.entry.sample.temperature = 40.0
    >>> root.entry.sample.temperature.units = 'K'
    >>> root.save('example.nxs')

:class:`NXfield` objects have much of the functionality of Numpy arrays. They may be used
in simple arithmetic expressions with other NXfields, Numpy arrays or scalar
values and will be cast as ndarray objects if used as arguments in Numpy
modules.

    >>> x=nx.NXfield(np.linspace(0,10.0,11))
    >>> x
    NXfield([  0.   1.   2. ...,   8.   9.  10.])
    >>> x + 10
    NXfield([ 10.  11.  12. ...,  18.  19.  20.])
    >>> np.sin(x)
    array([ 0.        ,  0.84147098,  0.90929743, ...,  0.98935825,
        0.41211849, -0.54402111])

If the arithmetic operation is assigned to a NeXus group attribute, it will be
automatically cast as a valid :class:`NXfield` object with the type and shape determined
by the Numpy array type and shape.

    >>> entry.data.result = np.sin(x)
    >>> entry.data.result
    NXfield([ 0.          0.84147098  0.90929743 ...,  0.98935825  0.41211849
     -0.54402111])
    >>> entry.data.result.dtype, entry.data.result.shape
    (dtype('float64'), (11,))

NeXus Objects
-------------
Properties of the entry in the tree are referenced by attributes that depend
on the object type, different nx attributes may be available.

Objects (:class:`NXobject`) have attributes shared by both groups and fields::
    * nxname   object name
    * nxclass  object class for groups, 'NXfield' for fields
    * nxgroup  group containing the entry, or None for the root
    * attrs    dictionary of NeXus attributes for the object

Groups (:class:`NXgroup`) have attributes for accessing children::
    * entries  dictionary of entries within the group
    * component('nxclass')  return group entries of a particular class
    * dir()    print the list of entries in the group
    * tree     return the list of entries and subentries in the group
    * plot()   plot signal and axes for the group, if available

Fields (:class:`NXfield`) have attributes for accessing data:
    * shape    dimensions of data in the field
    * dtype    data type
    * nxdata   data in the field

Linked fields or groups (:class:`NXlink`) have attributes for accessing the link::
    * nxlink   reference to the linked field or group

NeXus attributes (:class:`NXattr`) have a type and a value only::
    * dtype    attribute type
    * nxdata   attribute data

There is a subclass of :class:`NXgroup` for each group class defined by the NeXus standard,
so it is possible to create an :class:`NXgroup` of NeXus :class:`NXsample` directly using:

    >>> sample = NXsample()

The default group name will be the class name following the 'NX', so the above
group will have an nxname of 'sample'. However, this is overridden by the
attribute name when it is assigned as a group attribute, e.g.,

    >>> entry.sample1 = NXsample()
    >>> entry.sample1.nxname
    sample1

You can traverse the tree by component class instead of component name. Since
there may be multiple components of the same class in one group you will need to
specify which one to use.  For example::

    tree.NXentry[0].NXinstrument[0].NXdetector[0].distance

references the first detector of the first instrument of the first entry.
Unfortunately, there is no guarantee regarding the order of the entries, and it
may vary from call to call, so this is mainly useful in iterative searches.


Unit Conversion
---------------
Data can be stored in the NeXus file in a variety of units, depending on which
facility is storing the file.  This makes life difficult for reduction and
analysis programs which must know the units they are working with.  Our solution
to this problem is to allow the reader to retrieve data from the file in
particular units.  For example, if detector distance is stored in the file using
millimeters you can retrieve them in meters using::

    entry.instrument.detector.distance.convert('m')

See `nexus.unit` for more details on the unit formats supported.

Reading and Writing Slabs
-------------------------
If the size of the :class:`NXfield` array is too large to be loaded into memory (as 
defined by NX_MEMORY), the data values should be read or written in as a series 
of slabs represented by :class:`NXfield` slices::

 >>> for i in range(Ni):
         for j in range(Nj):
             value = root.NXentry[0].data.data[i,j,:]
             ...


Plotting NeXus data
-------------------
There is a :meth:`plot()` method for groups that automatically looks for 'signal' and
'axes' attributes within the group in order to determine what to plot. These are
defined by the 'nxsignal' and 'nxaxes' properties of the group. This means that
the method will determine whether the plot should be one- or two- dimensional.
For higher than two dimensions, only the top slice is plotted by default.

The plot method accepts as arguments the standard matplotlib.pyplot.plot format 
strings to customize one-dimensional plots, axis and scale limits, and will
transmit keyword arguments to the matplotlib plotting methods.

    >>> a=nx.load('chopper.nxs')
    >>> a.entry.monitor1.plot()
    >>> a.entry.monitor2.plot('r+', xmax=2600)
    
It is possible to plot over the existing figure with the :meth:`oplot()` method and to
plot with logarithmic intensity scales with the :meth:`logplot()` method. The x- and
y-axes can also be rendered logarithmically using the `logx` and `logy` keywords.

Although the :meth:`plot()` method uses matplotlib by default to plot the data, you can replace
this with your own plotter by setting `nexus.NXgroup._plotter` to your own plotter
class.  The plotter class has one method::

    plot(signal, axes, entry, title, format, **kwargs)

where signal is the field containing the data, axes are the fields listing the
signal sample points, entry is file/path within the file to the data group and
title is the title of the group or the parent :class:`NXentry`, if available.
"""
from __future__ import absolute_import, division, print_function

import numbers
import os
import re
import sys
import warnings
from copy import copy, deepcopy

import h5py as h5
import numpy as np
import six

from .. import __version__ as nxversion
from .lock import NXLock, NXLockException

warnings.simplefilter(action='ignore', category=FutureWarning)

NX_MEMORY = 2000 #Memory in MB
NX_COMPRESSION = 'gzip'
NX_ENCODING = sys.getfilesystemencoding()
NX_MAXSIZE = 10000
NX_LOCK = 0

np.set_printoptions(threshold=5)
string_dtype = h5.special_dtype(vlen=six.text_type)

__all__ = ['NXFile', 'NXobject', 'NXfield', 'NXgroup', 'NXattr', 
           'NXlink', 'NXlinkfield', 'NXlinkgroup', 'NeXusError', 
           'nxgetlock', 'nxsetlock', 'nxgetmemory', 'nxsetmemory', 
           'nxgetcompression', 'nxsetcompression', 
           'nxgetencoding', 'nxsetencoding', 'nxgetmaxsize', 'nxsetmaxsize',
           'nxclasses', 'nxload', 'nxsave', 'nxduplicate', 'nxdir', 'nxdemo',
           'nxversion']

#List of defined base classes (later added to __all__)
nxclasses = ['NXroot', 'NXentry', 'NXsubentry', 'NXdata', 'NXmonitor', 'NXlog', 
             'NXsample', 'NXinstrument', 'NXaperture', 'NXattenuator', 'NXbeam', 
             'NXbeam_stop', 'NXbending_magnet', 'NXcapillary', 'NXcite',
             'NXcollection', 'NXcollimator', 'NXcrystal', 'NXdetector', 
             'NXdetector_group', 'NXdetector_module', 'NXdisk_chopper', 
             'NXenvironment', 'NXevent_data', 'NXfermi_chopper', 'NXfilter', 
             'NXflipper', 'NXgeometry', 'NXgrating', 'NXgoniometer', 'NXguide', 
             'NXinsertion_device', 'NXmirror', 'NXmoderator', 'NXmonochromator', 
             'NXnote', 'NXorientation', 'NXparameters', 'NXpinhole', 
             'NXpolarizer', 'NXpositioner', 'NXprocess', 'NXreflections', 
             'NXsample_component', 'NXsensor', 'NXshape', 'NXslit', 'NXsource', 
             'NXtransformations', 'NXtranslation', 'NXuser', 
             'NXvelocity_selector', 'NXxraylens']

if six.PY2:
    FileNotFoundError = IOError
else:
    unicode = str


def text(value):
    """Return a unicode string in both Python 2 and 3.
    
    Parameters
    ----------
    value : str or bytes
        String or byte array to be converted.
    
    Returns
    -------
    str
        Converted unicode string
    
    Notes
    -----
    If the argument is a byte array, the function will decode the array using
    the encoding specified by NX_ENCODING, which is initially set to the
    system's default encoding, usually 'utf-8'. If this generates a 
    UnicodeDecodeError exception, an alternate encoding is tried. Null 
    characters are removed from the return value.
    """
    if isinstance(value, np.ndarray) and value.shape == (1,):
        value = value[0]
    if isinstance(value, bytes):
        try:
            text = value.decode(NX_ENCODING)
        except UnicodeDecodeError:
            if NX_ENCODING == 'utf-8':
                text = value.decode('latin-1')
            else:
                text = value.decode('utf-8')
    elif six.PY3:
        text = str(value)
    else:
        text = unicode(value)
    return text.replace('\x00','').rstrip()


def is_text(value):
    """Return True if the value represents text in both Python 2 and 3.
    
    Parameters
    ----------
    value : str or bytes
        Value to be checked.
    
    Returns
    -------
    bool
        True if the value is a string or bytes array.
    """
    if isinstance(value, bytes) or isinstance(value, six.string_types):
        return True
    else:
        return False


def is_string_dtype(dtype):
    """Return True if the dtype corresponds to a string type.
    
    Parameters
    ----------
    dtype : np.dtype
        Numpy data type to be tested.
    
    Returns
    -------
    bool
        True if the dtype corresponds to a string type.
    """
    return dtype == string_dtype or dtype.kind == 'S' or dtype.kind == 'U'


def is_iterable(obj):
    """Return True if the object is a list or a tuple.
    
    Parameters
    ----------
    obj : list or tuple
        Object to be tested.
    
    Returns
    -------
    bool
        True if the object is a list or a tuple.
    """
    return isinstance(obj, list) or isinstance(obj, tuple)


def natural_sort(key):
    """Key to sort a list of strings containing numbers in natural order.

    This function is used to customize the sorting of lists of strings. For 
    example, it ensures that 'label_10' follows 'label_9' after sorting.
    
    Parameters
    ----------
    key : str
        String in the list to be sorted.
    
    Returns
    -------
    list
        List of string components splitting embedded numbers as integers.
    """
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', key)]    


class NeXusError(Exception):
    """NeXus Error"""
    pass


class NXFile(object):
    """
    Structure-based interface to the NeXus file API.

    Usage::

      file = NXFile(filename, ['r','rw','w'])
        - open the NeXus file
      root = file.readfile()
        - read the structure of the NeXus file.  This returns a NeXus tree.
      file.writefile(root)
        - write a NeXus tree to the file.

    Example::

      nx = NXFile('REF_L_1346.nxs','r')
      root = nx.readfile()
      for entry in root.NXentry:
          process(entry)
      copy = NXFile('modified.nxs','w')
      copy.writefile(root)

    Note that the large datasets are not loaded immediately.  Instead, the
    when the data set is requested, the file is reopened, the data read, and
    the file closed again.  open/close are available for when we want to
    read/write slabs without the overhead of moving the file cursor each time.
    The :class:`NXdata` objects in the returned tree hold the object values.
    """

    def __init__(self, name, mode='r', **kwargs):
        """Open an HDF5 file for reading and writing NeXus files.

        This creates a h5py File instance that is used for all subsequent
        input and output. Unlike h5py, where a closed file is no longer 
        accessible, the NXFile instance is persistent, and can be used to
        with a context manager to ensure that all file operations are 
        completed and the h5py File is released. A file locking mechanism
        is optionally available to prevent corruption of the file when 
        being accessed by multiple processes.
        
        Parameters
        ----------
        name : str
            Name of the HDF5 file.
        mode : {'r', 'rw', 'r+', 'w', 'w-', 'a'}
            Read/write mode of the HDF5 file, by default 'r'. These all have 
            the same meaning as their h5py counterparts, apart from 'rw', 
            which is equivelent to 'r+'. After creating and/or opening the 
            file, the mode is set to 'r' or 'rw' for remaining operations.
        """
        self.h5 = h5
        self.name = name
        self._file = None
        self._filename = os.path.abspath(name)
        self._lock = NXLock(self._filename, timeout=NX_LOCK)
        self._path = '/'
        self._root = None
        self._with_count = 0
        if mode == 'w4' or mode == 'wx':
            raise NeXusError("Only HDF5 files supported")
        elif not os.path.exists(os.path.dirname(self._filename)):
            raise NeXusError("'%s/' does not exist"
                             % os.path.dirname(self._filename))
        elif mode == 'w' or mode == 'w-' or mode == 'w5' or mode == 'a' or mode == 'x':
            if mode == 'w5':
                mode = 'w'
            try:
                self._file = self.h5.File(self._filename, mode, **kwargs)
            except Exception as error:
                raise NeXusError(str(error))
            self._mode = 'rw'
        else:
            if mode == 'rw' or mode == 'r+':
                self._mode = 'rw'
                mode = 'r+'
            else:
                self._mode = 'r'
            if os.path.exists(name):
                try:
                    self._file = self.h5.File(self._filename, mode, **kwargs)
                except Exception as error:
                    raise NeXusError(str(error))
            else:
                raise NeXusError("'%s' does not exist" % name)
        self._file.close()

    def __repr__(self):
        return '<NXFile "%s" (mode %s)>' % (os.path.basename(self._filename),
                                            self._mode)

    def __getitem__(self, key):
        """Return an object from the NeXus file using its path."""
        return self.file.get(key)

    def __setitem__(self, key, value):
        """Set the value of an object defined by its path in the NeXus file."""
        self.file[key] = value

    def __delitem__(self, name):
        """ Delete an object from the file. """
        del self.file[name]

    def __contains__(self, key):
        """Implement 'k in d' test for entries in the file."""
        return self.file.__contains__(key)

    def __enter__(self):
        if self._with_count == 0:
            self.acquire_lock()
            self.open()
        self._with_count += 1
        return self

    def __exit__(self, *args):
        if self._with_count == 1:
            self.close()
            self.release_lock()
        self._with_count -= 1

    def __del__(self):
        self.close()
        self.release_lock()

    @property
    def root(self):
        """Return the root group of the NeXus file."""
        return self._root
    
    @property
    def mtime(self):
        """Return the modification time of the NeXus file."""
        return os.path.getmtime(self._filename)
    
    @property
    def lock(self):
        """Return the NXLock instance to be used in file locking.

        The global variable, `NX_LOCK`, defines the default timeout in
        seconds of attempts to acquire the lock. If it is set to 0, the 
        NXFile object is not locked by default. The `lock` property can 
        be set to turn on file locking, either by setting it to a new
        timeout value or by setting it to `True`, in which case a default 
        timeout of 10 seconds is used.

        Returns
        -------
        NXLock
            Instance of the file lock.
        """
        return self._lock

    @lock.setter
    def lock(self, value):
        if self._lock is None:
            self._lock = NXLock(self._filename, timeout=NX_LOCK)
        if value is False or value is None or value == 0:
            self._lock.timeout = 0
        else:
            if value is True:
                if NX_LOCK:
                    timeout = NX_LOCK
                else:
                    timeout = 10
            else:
                timeout = value
            self._lock.timeout=timeout

    @property
    def locked(self):
        """Return True if a file lock is active in the current process."""
        return self._lock is not None and self._lock.locked

    @property
    def lock_file(self):
        """Return the name of the file used to establish the lock."""
        if self._lock is None:
            self._lock = NXLock(self._filename, timeout=NX_LOCK)
        return self._lock.lock_file

    def acquire_lock(self, timeout=None):
        """Acquire the file lock.

        This uses the NXLock instance returned by `self.lock`.
        
        Parameters
        ----------
        timeout : int, optional
            Timeout for attempts to acquire the lock, by default None.
        """
        if self.locked and self.is_locked():
            return
        if self._lock is None:
            if timeout is not None:
                self.lock = timeout
            elif NX_LOCK:
                self.lock = NX_LOCK
            elif self.is_locked():
                self.lock = True
            if self._lock is None:
                return
        self._lock.acquire()

    def release_lock(self):
        """Release the lock acquired by the current process."""
        if self.locked:
            self._lock.release()

    def wait_lock(self, timeout=True):
        """Wait for a file lock created by an external process to be cleared.
        
        Parameters
        ----------
        timeout : bool or int, optional
            The value, in seconds, of the time to wait. If set to `True`, a
            default value of 10 seconds is used.
        """
        self.lock = timeout
        NXLock(self._filename, timeout=timeout).wait()

    def clear_lock(self, timeout=True):
        """Clear the file lock whether created by this or another process.

        Note
        ----
        Since the use of this function implies that another process is 
        accessing this file, file locking is turned on for future 
        input/output. The `timeout` value applies to future access. The
        existing lock is cleared immediately.
        
        Parameters
        ----------
        timeout : bool or int, optional
            The value, in seconds, of the time to wait for future file locks. 
            If set to `True`, a default value of 10 seconds is used.
        """
        if self.is_locked():
            self.lock = timeout
            self._lock.clear()

    def is_locked(self):
        """Return True if a lock file exists for this NeXus file."""
        return os.path.exists(self.lock_file)

    def get(self, *args, **kwargs):
        return self.file.get(*args, **kwargs)

    def copy(self, *args, **kwargs):
        self.file.copy(*args, **kwargs)

    def open(self, **kwargs):
        if not self.isopen():
            if self._mode == 'rw':
                self._file = self.h5.File(self._filename, 'r+', **kwargs)
            else:
                self._file = self.h5.File(self._filename, self._mode, **kwargs)
            self.nxpath = '/'

    def close(self):
        if self.isopen():
            self._file.close()
        if self._root:
            self._root._mtime = self.mtime

    def isopen(self):
        if self._file is not None:
            return self._file.id.valid
        else:
            return False

    def readfile(self):
        """
        Reads the NeXus file structure from the file and returns a tree of 
        NXobjects.

        Large datasets are not read until they are needed.
        """
        _mode = self._mode
        self._mode = 'r'
        self.nxpath = '/'
        root = self._readgroup('root')
        root._group = None
        root._file = self
        root._filename = self._filename
        root._mode = self._mode = _mode
        root._file_modified = False
        self._root = root
        return root

    def _readattrs(self):
        item = self.get(self.nxpath)
        if item is not None:
            attrs = {}
            for key in item.attrs:
                try:
                    attrs[key] = item.attrs[key]
                except Exception:
                    attrs[key] = None
            return attrs
        else:
            return {}

    def _readchildren(self):
        children = {}
        items = self[self.nxpath].items()
        for name, value in items:
            self.nxpath = self.nxpath + '/' + name
            if isinstance(value, self.h5.Group):
                children[name] = self._readgroup(name)
            elif isinstance(value, self.h5.Dataset):
                children[name] = self._readdata(name)
            else:
                _link = self._readlink(name)
                if _link:
                    children[name] = _link
            self.nxpath = self.nxparent
        return children

    def _readgroup(self, name):
        """
        Reads the group with the current path and returns it as an NXgroup.
        """
        attrs = self._readattrs()
        nxclass = self._getclass(attrs.pop('NX_class', 'NXgroup'))
        if nxclass == 'NXgroup' and self.nxpath == '/':
            nxclass = 'NXroot'
        children = self._readchildren()
        _target, _filename, _abspath = self._getlink()
        if _target is not None:
            group = NXlinkgroup(nxclass=nxclass, name=name, attrs=attrs,
                                new_entries=children, target=_target,
                                file=_filename, abspath=_abspath)
        else:
            group = NXgroup(nxclass=nxclass, name=name, attrs=attrs,
                            new_entries=children)
        for obj in children.values():
            obj._group = group
        group._changed = True
        return group

    def _readdata(self, name):
        """
        Reads a data object and returns it as an NXfield or NXlink.
        """
        _target, _filename, _abspath = self._getlink()
        if _target is not None:
            if _filename is not None:
                try:
                    value, shape, dtype, attrs = self.readvalues()
                    return NXlinkfield(
                        target=_target, file=_filename, abspath=_abspath,
                        name=name, value=value, dtype=dtype, shape=shape, 
                        attrs=attrs)
                except Exception:
                    pass
            return NXlinkfield(name=name, target=_target, file=_filename, 
                               abspath=_abspath)
        else:
            value, shape, dtype, attrs = self.readvalues()
            return NXfield(value=value, name=name, dtype=dtype, shape=shape, 
                           attrs=attrs)

    def _readlink(self, name):
        """
        Reads an object that is an undefined link.
        
        This is usually an external link to a non-existent file. It can also be
        a link to an unresolved external link.
        """
        _target, _filename, _abspath = self._getlink()
        if _target is not None:
            return NXlink(name=name, target=_target, file=_filename, 
                          abspath=_abspath)
        else:
            return None
 
    def _getclass(self, nxclass):
        nxclass = text(nxclass)
        if nxclass is None:
            return 'NXgroup'
        else:
            return nxclass

    def _getlink(self):
        _target, _filename, _abspath = None, None, False
        if self.nxpath != '/':
            _link = self.get(self.nxpath, getlink=True)
            if isinstance(_link, h5.ExternalLink):
                _target, _filename = _link.path, _link.filename
                _abspath = os.path.isabs(_filename)
            elif isinstance(_link, h5.SoftLink):
                _target = _link.path
            elif 'target' in self.attrs:
                _target = text(self.attrs['target'])
                if _target == self.nxpath:
                    _target = None
        return _target, _filename, _abspath

    def writefile(self, root):
        """
        Writes the NeXus file structure to a file.

        The file is assumed to start empty. Updating individual objects can be
        done using the h5py interface.
        """
        links = []
        self.nxpath = ""
        for entry in root.values():
            links += self._writegroup(entry)
        self._writelinks(links)
        if len(root.attrs) > 0:
            self._writeattrs(root.attrs)
        root._filename = self._filename
        self._root = root
        self._rootattrs()

    def _writeattrs(self, attrs):
        """
        Writes the attributes for the group/data with the current path.

        Null attributes are ignored.
        """
        if self[self.nxpath] is not None:
            for name, value in attrs.items():
                if value.nxdata is not None:
                    self[self.nxpath].attrs[name] = value.nxdata

    def _writegroup(self, group):
        """
        Writes the given group structure, including the data.

        Internal NXlinks cannot be written until the linked group is created, 
        so this routine returns the set of links that need to be written.
        Call writelinks on the list.
        """
        if group.nxpath != '' and group.nxpath != '/':
            self.nxpath = self.nxpath + '/' + group.nxname
            if group.nxname not in self[self.nxparent]:
                if group._target is not None:
                    if group._filename is not None:
                        self.nxpath = self.nxparent
                        self._writeexternal(group)
                        self.nxpath = self.nxparent
                        return []
                else:
                    self[self.nxparent].create_group(group.nxname)
            if group.nxclass and group.nxclass != 'unknown':
                self[self.nxpath].attrs['NX_class'] = group.nxclass
        links = []
        self._writeattrs(group.attrs)
        if group._target is not None:
            links += [(self.nxpath, group._target)]
        for child in group.values():
            if isinstance(child, NXlink):
                if child._filename is not None:
                    self._writeexternal(child)
                else:
                    links += [(self.nxpath+"/"+child.nxname, child._target)]
            elif isinstance(child, NXfield):
                links += self._writedata(child)
            else:
                links += self._writegroup(child)
        self.nxpath = self.nxparent
        return links

    def _writedata(self, data):
        """
        Writes the given data to a file.

        NXlinks cannot be written until the linked group is created, so
        this routine returns the set of links that need to be written.
        Call writelinks on the list.
        """
        self.nxpath = self.nxpath + '/' + data.nxname
        # If the data is linked then
        if data._target is not None:
            if data._filename is not None:
                self._writeexternal(data)
                self.nxpath = self.nxparent
                return []
            else:
                path = self.nxpath
                self.nxpath = self.nxparent
                return [(path, data._target)]
        if data._uncopied_data:
            if self.nxpath in self:
                del self[self.nxpath]
            _file, _path = data._uncopied_data
            if _file._filename != self._filename:
                with _file as f:
                    f.copy(_path, self[self.nxparent], self.nxpath)
            else:
                self.file.copy(_path, self[self.nxparent], self.nxpath)
            data._uncopied_data = None
        elif data._memfile:
            data._memfile.copy('data', self[self.nxparent], self.nxpath)
            data._memfile = None
        elif data.nxfile and data.nxfile.filename != self.filename:
            data.nxfile.copy(data.nxpath, self[self.nxparent])
        elif data.dtype is not None:
            if data.nxname not in self[self.nxparent]:
                self[self.nxparent].create_dataset(data.nxname, 
                                                   shape=data.shape, dtype=data.dtype,
                                                   **data._h5opts)
            try:
                if data._value is not None:
                    self[self.nxpath][()] = data._value 
            except NeXusError:
                pass
        self._writeattrs(data.attrs)
        self.nxpath = self.nxparent
        return []

    def _writeexternal(self, item):
        self.nxpath = self.nxpath + '/' + item.nxname
        if item._abspath:
            filename = item.nxfilename
        elif os.path.isabs(item._filename):
            filename = os.path.relpath(os.path.realpath(item._filename), 
                           os.path.dirname(os.path.realpath(self.filename)))
        else:
            filename = item._filename
        self[self.nxpath] = self.h5.ExternalLink(filename, item._target)
        self.nxpath = self.nxparent

    def _writelinks(self, links):
        """
        Creates links within the NeXus file.

        These are defined by the set of pairs returned by _writegroup.
        """
        # link sources to targets
        for path, target in links:
            if path != target and path not in self['/'] and target in self['/']:
                if 'target' not in self[target].attrs:
                    self[target].attrs['target'] = target
                self[path] = self[target]

    def readpath(self, path):
        self.nxpath = path
        return self.readitem()

    def readitem(self):
        item = self.get(self.nxpath)
        if isinstance(item, self.h5.Group):
            return self._readgroup(self.nxname)
        else:
            return self._readdata(self.nxname)

    def readvalues(self, attrs=None):
        field = self.get(self.nxpath)
        if field is None:
            return None, None, None, {}
        shape, dtype = field.shape, field.dtype
        #Read in the data if it's not too large
        if np.prod(shape) < 1000:# i.e., less than 1k dims
            try:
                value = self.readvalue(self.nxpath)
            except Exception as error:
                value = None
        else:
            value = None
        if attrs is None:
            attrs = self.attrs
            if 'NX_class' in attrs and text(attrs['NX_class']) == 'SDS':
                attrs.pop('NX_class')
        return value, shape, dtype, attrs

    def readvalue(self, path, idx=()):
        field = self.get(path)
        if field is not None:
            return field[idx]
        return None

    def writevalue(self, path, value, idx=()):
        self[path][idx] = value

    def copyfile(self, input_file, **kwargs):
        for entry in input_file['/']:
            input_file.copy(entry, self['/'], **kwargs) 
        self._rootattrs()

    def _rootattrs(self):
        from datetime import datetime
        self.file.attrs['file_name'] = self.filename
        self.file.attrs['file_time'] = datetime.now().isoformat()
        self.file.attrs['HDF5_Version'] = self.h5.version.hdf5_version
        self.file.attrs['h5py_version'] = self.h5.version.version
        from .. import __version__
        self.file.attrs['nexusformat_version'] = __version__

    def update(self, item):
        self.nxpath = item.nxpath
        if isinstance(item, AttrDict):
            self._writeattrs(item)
        else:
            self.nxpath = self.nxparent
            if isinstance(item, NXlink):
                if item._filename is None:
                    self._writelinks([(item.nxpath, item._target)])
                else:
                    self._writeexternal(item)
            elif isinstance(item, NXfield):
                self._writedata(item)
            elif isinstance(item, NXgroup):
                links = self._writegroup(item)
                self._writelinks(links)
            self.nxpath = item.nxpath

    def reload(self):
        self.nxpath = '/'
        self._root._entries = self._readchildren()
        for entry in self._root._entries:
            self._root._entries[entry]._group = self._root
        self._root._changed = True
        self._root._file_modified = False

    def rename(self, old_path, new_path):
        if old_path != new_path:
            self.file['/'].move(old_path, new_path)

    @property
    def filename(self):
        """File name on disk"""
        return self.file.filename

    @property
    def file(self):
        if not self.isopen():
            self.open()
        return self._file

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if mode == 'rw' or mode == 'r+':
            self._mode = 'rw'
        else:
            self._mode = 'r'   
        self.close()

    @property
    def attrs(self):
        return self._readattrs()

    @property
    def nxpath(self):
        return self._path.replace('//','/')

    @nxpath.setter
    def nxpath(self, value):
        self._path = value.replace('//','/')

    @property
    def nxparent(self):
        return '/' + self.nxpath[:self.nxpath.rfind('/')].lstrip('/')

    @property
    def nxname(self):
        return self.nxpath[self.nxpath.rfind('/')+1:]


def _makeclass(cls, bases=None):
    docstring = """
                %s group. This is a subclass of the NXgroup class.

                See the NXgroup documentation for more details.
                """ % cls
    if bases is None:
        bases = (NXgroup,)
    return type(str(cls), bases, {'_class':cls, '__doc__':docstring})


def _getclass(cls, link=False):
    if isinstance(cls, type):
        cls = cls.__name__
    if not cls.startswith('NX'):
        return type(object)
    elif cls in globals() and (not link or cls.startswith('NXlink')):
        return globals()[cls]
    if cls != 'NXlink' and cls.startswith('NXlink'):
        link = True
        cls = cls.replace('NXlink', 'NX')
    if link:
        if cls in globals():
            bases = (NXlinkgroup, globals()[cls])
            cls = cls.replace('NX', 'NXlink')
            globals()[cls] = _makeclass(cls, bases)
        else:
            raise NeXusError("'%s' is not a valid NeXus class" % cls)
    else:
        globals()[cls] = _makeclass(cls, (NXgroup,))
    return globals()[cls]


def _getvalue(value, dtype=None, shape=None):
    """
    Returns a value, dtype and shape based on the input Python value. If the
    value is a string, it is converted to unicode. Otherwise, the value is 
    converted to a valid Numpy object.
    
    If the value is a masked array, the returned value is only returned as a 
    masked array if some of the elements are masked.

    If 'dtype' and/or 'shape' are specified as input arguments, the value is 
    converted to the given dtype and/or reshaped to the given shape. Otherwise, 
    the dtype and shape are determined from the value.
    """
    dtype, shape = _getdtype(dtype), _getshape(shape)
    if isinstance(value, NXfield) or isinstance(value, NXattr):
        value = value.nxvalue
    if value is None:
        return None, dtype, shape
    elif is_text(value):
        if shape is not None and shape != ():
            raise NeXusError("The value is incompatible with the shape")
        if dtype is not None:
            try:
                _dtype = _getdtype(dtype)
                if _dtype.kind == 'S':
                    value = text(value).encode('utf-8')
                return np.array(value, dtype=_dtype).item(), _dtype, ()
            except Exception:
                raise NeXusError("The value is incompatible with the dtype")
        else:
            _value = text(value)
            if _value == u'':
                _value = u' '
            return _value, string_dtype, ()
    elif isinstance(value, np.ndarray):
        if isinstance(value, np.ma.MaskedArray):
            if value.count() < value.size: #some values are masked
                _value = value
            else:
                _value = np.asarray(value)
        else:
            _value = np.asarray(value) #convert subclasses of ndarray
    else:
        try:
            _value = [np.asarray(v) for v in value]
            if len(set([v.shape for v in _value])) > 1:
                raise NeXusError(
                    "Cannot assign an iterable with items of multiple shapes")
            _value = np.asarray(_value)
        except TypeError:
            _value = np.asarray(value)
        if _value.dtype.kind == 'S' or _value.dtype.kind == 'U':
            _value = _value.astype(string_dtype)
    if dtype is not None:
        if isinstance(value, np.bool_) and dtype != np.bool_:
            raise NeXusError(
                "Cannot assign a Boolean value to a non-Boolean field")
        elif isinstance(_value, np.ndarray):
            try:
                _value = _value.astype(dtype)
            except:
                raise NeXusError("The value is incompatible with the dtype")
    if shape is not None and isinstance(_value, np.ndarray):
        try:
            _value = _value.reshape(shape)
        except ValueError:
            raise NeXusError("The value is incompatible with the shape")
    if _value.shape == ():
        return _value.item(), _value.dtype, _value.shape
    else:
        return _value, _value.dtype, _value.shape


def _getdtype(dtype):
    """Return a valid h5py dtype.

    This converts string dtypes to the special HDF5 dtype for variable length 
    strings. Other values are checked against valid Numpy dtypes.
    
    Parameters
    ----------
    dtype : dtype
        Proposed datatype of an NXfield.
    
    Returns
    -------
    dtype
        Valid dtype for storing in an HDF5 file.
    """
    if dtype is None:
        return None
    elif is_text(dtype) and dtype == 'char':
        return string_dtype
    else:
        try:
            _dtype = np.dtype(dtype)
            if _dtype.kind == 'U':
                return string_dtype
            else:
                return _dtype
        except TypeError:
            raise NeXusError("Invalid data type: %s" % dtype)


def _getshape(shape, maxshape=False):
    """Return valid shape tuple.

    The returned shape tuple will contain integer values, unless maxshape is
    True, in which case, values of None are allowed.
    
    Parameters
    ----------
    shape : tuple of int
        Proposed new shape
    maxshape : bool, optional
        True if values of None are permitted in a shape element,
        by default False
    
    Returns
    -------
    tuple of int
        Valid shape tuple.
    """
    if shape is None:
        return None
    else:
        try:
            if not is_iterable(shape):
                shape = [shape]       
            if maxshape:
                return tuple([None if i is None else int(i) for i in shape])
            elif None in shape:
                return None
            else:
                return tuple([int(i) for i in shape])
        except ValueError:
            raise NeXusError("Invalid shape: %s" % str(shape))

    
def _getmaxshape(maxshape, shape):
    """Return maximum shape if compatible with the specified shape.

    This raises a NeXusError if the length of the shapes do not match or if
    any of the elements in maxshape are smaller than the corresponding 
    element in shape. If maxshape has a size of 1, an empty tuple is returned.
    
    Parameters
    ----------
    maxshape : tuple of int
        Proposed maximum shape of the array
    shape : tuple of int
        Current shape of the array
    
    Returns
    -------
    tuple of int
        Maximum shape
    """
    maxshape, shape = _getshape(maxshape, maxshape=True), _getshape(shape)
    if maxshape is None or shape is None:
        return None
    else:
        if maxshape == (1,) and shape == ():
            return ()
        elif len(maxshape) != len(shape):
            raise NeXusError(
            "Number of dimensions in maximum shape does not match the field")
        else:
            if _checkshape(shape, maxshape):
                return maxshape
            else:
                raise NeXusError("Maximum shape must be larger than the field shape")


def _checkshape(shape, maxshape):
    """Return True if the shape is consistent with the maximum allowed shape.

    Each element of shape must be less than or equal to the 
    corresponding element of maxshape, unless the latter is set to None, in 
    which case the value of the shape element is unlimited.
    
    Parameters
    ----------
    shape : tuple of int
        Shape to be checked.
    maxshape : tuple of int
        Maximum allowed shape
    
    Returns
    -------
    bool
        True if the shape is consistent.
    """
    for i, j in [(_i, _j) for _i, _j in zip(maxshape, shape)]:
        if i is not None and i < j:
            return False
    return True

    
def _getsize(shape):
    """Return the total size of the array with the specified shape.

    If the shape is None, a size of 1 is returned.
    
    Parameters
    ----------
    shape : tuple of int
        Shape of the array.
    
    Returns
    -------
    int
        Size of the array
    """
    if shape is None:
        return 1
    else:
        try:
            return np.prod(shape)
        except Exception:
            return 1

    
def _readaxes(axes):
    """
    Returns a list of axis names stored in the 'axes' attribute.

    The delimiter separating each axis can be white space, a comma, or a colon.
    """
    if is_text(axes):
        return list(re.split(r'[,:; ]', 
                    text(axes).strip('[]()').replace('][', ':')))
    else:
        return [text(axis) for axis in axes]


class AttrDict(dict):
    """A dictionary class used to assign and return values to NXattr instances.
    
    This is used to control the initialization of the NXattr objects and the
    return of their values. For example, attributes that contain string or byte
    arrays are returned as lists of (unicode) strings. Size-1 arrays are 
    returned as scalars. The 'get' function can be used to return the original 
    array. If the attribute are stored in a NeXus file with read/write access,
    their values are automatically updated.
    
    Parameters
    ----------
    parent : NXobject
        The field or group to which the attributes belong.
    attrs : dict
        A dictionary containing the first set of attributes.   
    """

    def __init__(self, parent=None, attrs={}):
        super(AttrDict, self).__init__()
        self._parent = parent
        self._setattrs(attrs)

    def _setattrs(self, attrs):
        for key, value in attrs.items():
            super(AttrDict, self).__setitem__(key, NXattr(value))
    
    def __getitem__(self, key):
        """Returns the value of the requested NXattr object."""
        return super(AttrDict, self).__getitem__(key).nxvalue

    def __setitem__(self, key, value):
        """Creates a new entry in the dictionary."""
        if value is None:
            return
        elif self._parent and self._parent.nxfilemode == 'w':
            raise NeXusError("NeXus file opened as readonly")
        if isinstance(value, NXattr):
            super(AttrDict, self).__setitem__(text(key), value)
        else:
            super(AttrDict, self).__setitem__(text(key), NXattr(value))
        if self._parent and self._parent.nxfilemode == 'rw':
            with self._parent.nxfile as f:
                f.update(self)

    def __delitem__(self, key):
        """Deletes an entry from the dictionary."""
        super(AttrDict, self).__delitem__(key)
        try:
            if self._parent.nxfilemode == 'rw':
                with self._parent.nxfile as f:
                    f.nxpath = self._parent.nxpath
                    del f[f.nxpath].attrs[key]
        except Exception:
            pass

    def get(self, key, default=None):
        """Retrieves the NXattr object stored in the dictionary."""
        try:
            return super(AttrDict, self).__getitem__(key)
        except KeyError:
            return default

    @property
    def nxpath(self):
        return self._parent.nxpath

class NXattr(object):
    """Class for NeXus attributes of a NXfield or NXgroup object.

    Attributes
    ----------
    nxvalue : string, Numpy scalar, or Numpy ndarray
        The value of the NeXus attribute modified as described below.
    nxdata : string, Numpy scalar, or Numpy ndarray
        The unmodified value of the NeXus attribute.
    dtype : string
        The data type of the NeXus attribute value.
    shape : tuple
        The shape of the NeXus attribute value.

    Note
    ----
    NeXus attributes are stored in the 'attrs' dictionary of the parent object,
    NXfield or NXgroup, but can often be referenced or assigned using the
    attribute name as if it were an object attribute.

    For example, after assigning the NXfield, the following three attribute
    assignments are all equivalent::

        >>> entry.sample.temperature = NXfield(40.0)
        >>> entry.sample.temperature.attrs['units'] = 'K'
        >>> entry.sample.temperature.units = NXattr('K')
        >>> entry.sample.temperature.units = 'K'

    The last version above is only allowed for NXfield attributes and is not 
    allowed if the attribute has the same name as one of the following
    internally defined attributes, i.e.,

    ['entries', 'attrs', 'dtype','shape']

    or if the attribute name begins with 'nx' or '_'. It is only possible to
    reference attributes with one of the proscribed names using the 'attrs'
    dictionary.
    """

    def __init__(self, value=None, dtype=None, shape=None):
        if isinstance(value, NXattr) or isinstance(value, NXfield):
            value = value.nxdata
        elif isinstance(value, NXgroup):
            raise NeXusError("A data attribute cannot be a NXgroup")
        self._value, self._dtype, self._shape = _getvalue(value, dtype, shape)

    def __str__(self):
        return text(self.nxvalue)

    def __unicode__(self):
        return text(self.nxvalue)

    def __repr__(self):
        if (self.dtype is not None and 
            (self.shape == () or self.shape == (1,)) and 
            (self.dtype.type == np.string_ or self.dtype.type == np.str_ or 
             self.dtype == string_dtype)):
            return "NXattr('%s')" % self
        else:
            return "NXattr(%s)" % self

    def __eq__(self, other):
        """Returns true if the values of the two attributes are the same."""
        if id(self) == id(other):
            return True
        elif isinstance(other, NXattr):
            return self.nxvalue == other.nxvalue
        else:
            return self.nxvalue == other

    def __hash__(self):
        return id(self)

    @property
    def nxvalue(self):
        """Returns the attribute value.
        
        This is the value stored in the NeXus file, with the following
        exceptions.
            1) Size-1 arrays are returned as scalars.
            2) String or byte arrays are returns as a list of strings.
        
        Note
        ----
        If unmodified values are required, use the 'nxdata' property.
        """
        if self._value is None:
            return ''
        elif (self.dtype is not None and
            (self.dtype.type == np.string_ or self.dtype.type == np.str_ or 
             self.dtype == string_dtype)):
            if self.shape == ():
                return text(self._value)
            elif self.shape == (1,):
                return text(self._value[0])
            else:
                return [text(value) for value in self._value[()]]
        elif self.shape == (1,):
            return self._value.item()
        else:
            return self._value

    @property
    def nxdata(self):
        """Returns the unmodified attribute value."""
        return self._value

    @property
    def dtype(self):
        return self._dtype

    @property
    def shape(self):
        try:
            return tuple([int(i) for i in self._shape])
        except (TypeError, ValueError):
            return ()


_npattrs = list(filter(lambda x: not x.startswith('_'), np.ndarray.__dict__))


class NXobject(object):

    """
    Abstract base class for elements in NeXus files.

    The object has a subclass of NXfield, NXgroup, or one of the NXgroup
    subclasses. Child nodes should be accessible directly as object attributes.
    Constructors for NXobject objects are defined by either the NXfield or
    NXgroup classes.

    **Python Attributes**

    nxclass : string
        The class of the NXobject. NXobjects can have class NXfield, NXgroup, or
        be one of the NXgroup subclasses.
    nxname : string
        The name of the NXobject. Since it is possible to reference the same
        Python object multiple times, this is not necessarily the same as the
        object name. However, if the object is part of a NeXus tree, this will
        be the attribute name within the tree.
    nxgroup : NXgroup
        The parent group containing this object within a NeXus tree. If the
        object is not part of any NeXus tree, it will be set to None.
    nxpath : string
        The path to this object with respect to the root of the NeXus tree. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.
    nxroot : NXgroup
        The root object of the NeXus tree containing this object. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.
    nxfile : NXFile
        The file handle of the root object of the NeXus tree containing this
        object.
    nxfilename : string
        The file name of NeXus object's tree file handle.
    attrs : dict
        A dictionary of the NeXus object's attributes.

    **Methods**

    dir(self, attrs=False, recursive=False):
        Print the group directory.

        The directory is a list of NeXus objects within this group, either NeXus
        groups or NXfield data. If 'attrs' is True, NXfield attributes are
        displayed. If 'recursive' is True, the contents of child groups are also
        displayed.

    tree:
        Return the object's tree as a string.

        It invokes the 'dir' method with both 'attrs' and 'recursive'
        set to True. Note that this is defined as a property attribute and
        does not require parentheses.

    save(self, filename, format='w')
        Save the NeXus group into a file

        The object is wrapped in an NXroot group (with name 'root') and an
        NXentry group (with name 'entry'), if necessary, in order to produce
        a valid NeXus file.

    """

    _class = "unknown"
    _name = "unknown"
    _group = None
    _attrs = AttrDict()
    _file = None
    _filename = None
    _abspath = False
    _target = None
    _external = None
    _mode = None
    _value = None
    _memfile = None
    _uncopied_data = None
    _changed = True
    _backup = None
    _file_modified = False

    def __getstate__(self):
        result = self.__dict__.copy()
        hidden_keys = [key for key in result if key.startswith('_')]
        needed_keys = ['_class', '_name', '_group', '_target', 
                       '_entries', '_attrs', '_filename', '_mode', 
                       '_dtype', '_shape', '_value', '_h5opts', '_changed']
        for key in hidden_keys:
            if key not in needed_keys:
                del result[key]
        return result

    def __setstate__(self, dict):
        self.__dict__ = dict

    def __str__(self):
        return "%s" % self.nxname

    def __repr__(self):
        return "NXobject('%s')" % (self.nxname)

    def __contains__(self, key):
        return False

    def _setattrs(self, attrs):
        for k,v in attrs.items():
            self._attrs[k] = v

    def walk(self):
        if False: 
            yield

    def _str_name(self, indent=0):
        return " " * indent + self.nxname

    def _str_attrs(self, indent=0):
        names = sorted(self.attrs)
        result = []
        for k in names:
            txt1 = u" " * indent
            txt2 = u"@" + k + " = "
            txt3 = text(self.attrs[k])
            if len(txt3) > 50:
                txt3 = txt3[:46] + '...'
            if is_text(self.attrs[k]):
                txt3 =  u"'" + txt3 + "'"
            else:
                txt3 = txt3
            txt = (txt1 + txt2 + txt3).replace("u'", "'")
            try:
                txt = txt[:txt.index('\n')]+'...'
            except ValueError:
                pass
            result.append(txt)
        return "\n".join(result)

    def _str_tree(self, indent=0, attrs=False, recursive=False):
        """
        Prints the current object and children (if any).
        """
        result = [self._str_name(indent=indent)]
        if self.attrs and (attrs or indent==0):
            result.append(self._str_attrs(indent=indent+2))
        return "\n".join(result)

    def dir(self, attrs=False, recursive=False):
        """
        Prints the object directory.

        The directory is a list of NeXus objects within this object, either
        NeXus groups or NXfields. If 'attrs' is True, NXfield attributes are
        displayed. If 'recursive' is True, the contents of child groups are
        also displayed.
        """
        print(self._str_tree(attrs=attrs, recursive=recursive))

    @property
    def tree(self):
        """
        Returns the directory tree as a string.

        The tree contains all child objects of this object and their children.
        It invokes the 'dir' method with 'attrs' set to False and 'recursive'
        set to True.
        """
        return self._str_tree(attrs=True, recursive=True)

    @property
    def short_tree(self):
        """
        Returns the directory tree as a string.

        The tree contains all child objects of this object and their children.
        It invokes the 'dir' method with 'attrs' set to False and 'recursive'
        set to True.
        """
        return self._str_tree(attrs=False, recursive=2)

    def rename(self, name):
        name = text(name)
        if name == self.nxname:
            return
        group = self.nxgroup
        if group is not None:
            if group.nxfilemode == 'r':
                raise NeXusError("NeXus parent group is readonly")
            else:
                signal = group.nxsignal
                axes = group.nxaxes
        elif self.nxfilemode == 'r':
            raise NeXusError("NeXus file opened as readonly")
        old_path = self.nxpath
        if group is not None:
            new_path = group.nxpath + '/' + name
            if not isinstance(self, NXroot) and group.nxfilemode == 'rw':
                with group.nxfile as f:
                    f.rename(old_path, new_path)
            group.entries[name] = group.entries.pop(self._name)
            if self is signal:
                group.nxsignal = self
            elif axes is not None:
                if [x for x in axes if x is self]:
                    group.nxaxes = axes
        self._name = name
        self.set_changed()

    def save(self, filename=None, mode='w-', **kwargs):
        """
        Saves the NeXus object to a data file.
        
        If the object is an NXroot group, this can be used to save the whole
        NeXus tree. If the tree was read from a file and the file was opened as
        read only, then a file name must be specified. Otherwise, the tree is
        saved to the original file. 
        
        An error is raised if the object is an NXroot group from an external 
        file that has been opened as readonly and no file name is specified.

        If the object is not an NXroot, group, a filename must be specified. The
        saved NeXus object is wrapped in an NXroot group (with name 'root') and 
        an NXentry group (with name 'entry'), if necessary, in order to produce 
        a valid NeXus file. Only the children of the object will be saved. This 
        capability allows parts of a NeXus tree to be saved for later use, e.g., 
        to store an NXsample group to be added to another file at a later time. 
        
        **Example**

        >>> data = NXdata(sin(x), x)
        >>> data.save('file.nxs')
        >>> print data.nxroot.tree
        root:NXroot
          @HDF5_Version = 1.8.2
          @NeXus_version = 4.2.1
          @file_name = file.nxs
          @file_time = 2012-01-20T13:14:49-06:00
          entry:NXentry
            data:NXdata
              axis1 = float64(101)
              signal = float64(101)
                @axes = axis1
                @signal = 1              
        >>> root.entry.data.axis1.units = 'meV'
        >>> root.save()
        """
        if filename:
            if os.path.splitext(filename)[1] not in ['.nxs', '.nx5', '.h5',
                                                     '.hdf', '.hdf5', '.cxi']:
                filename = filename + '.nxs'
            if self.nxclass == "NXroot":
                root = self
            elif self.nxclass == "NXentry":
                root = NXroot(self)
            else:
                root = NXroot(NXentry(self)) 
            if mode != 'w':
                write_mode = 'w-'
            else:
                write_mode = 'w'
            with NXFile(filename, write_mode, **kwargs) as f:
                f.writefile(root)
                root = f._root
                root._file = f
            if mode == 'w' or mode == 'w-':
                root._mode = 'rw'
            else:
                root._mode = mode
            self.set_changed()
            return root
        else:
            raise NeXusError("No output file specified")

    def update(self):
        if self.nxfilemode == 'rw':
            with self.nxfile as f:
                f.update(self)
        self.set_changed()

    @property
    def changed(self):
        """
        Property: Returns True if the object has been changed.
        
        This property is for use by external scripts that need to track
        which NeXus objects have been changed.
        """
        return self._changed
    
    def set_changed(self):
        """
        Sets an object's change status to changed.
        """
        self._changed = True
        if self.nxgroup:
            self.nxgroup.set_changed()
            
    def set_unchanged(self, recursive=False):
        """
        Sets an object's change status to unchanged.
        """
        if recursive:
            for node in self.walk():
                node._changed = False
        else:
            self._changed = False

    def _setclass(self, cls):
        try:
            class_ = _getclass(cls)
            if issubclass(class_, NXobject):
                self.__class__ = class_
                self._class = self.__class__.__name__
                if self._class.startswith('NXlink') and self._class != 'NXlink':
                    self._class = 'NX' + self._class[6:]
        except (TypeError, NameError):
            raise NeXusError("Invalid NeXus class")               
    
    @property
    def nxclass(self):
        return text(self._class)

    @nxclass.setter
    def nxclass(self, cls):
        self._setclass(cls)
        self.set_changed()

    @property
    def nxname(self):
        return text(self._name)

    @nxname.setter
    def nxname(self, value):
        self.rename(value)

    @property
    def nxgroup(self):
        return self._group

    @nxgroup.setter
    def nxgroup(self, value):
        if isinstance(value, NXgroup):
            self._group = value
        else:
            raise NeXusError("Value must be a valid NeXus group")    

    @property
    def nxpath(self):
        group = self.nxgroup
        if self.nxclass == 'NXroot':
            return "/"
        elif group is None:
            return self.nxname
        elif isinstance(group, NXroot):
            return "/" + self.nxname
        else:
            return group.nxpath+"/"+self.nxname

    @property
    def nxroot(self):
        if self._group is None or isinstance(self, NXroot):
            return self
        elif isinstance(self._group, NXroot):
            return self._group
        else:            
            return self._group.nxroot

    @property
    def nxentry(self):
        if self._group is None or isinstance(self, NXentry):
            return self
        elif isinstance(self._group, NXentry):
            return self._group
        else:
            return self._group.nxentry

    @property
    def nxfile(self):
        if self._file:
            return self._file
        elif not self.is_external() and self.nxroot._file:
            return self.nxroot._file
        elif self.nxfilename:
            self._file = NXFile(self.nxfilename, self.nxfilemode)
            return self._file
        else:
            return None

    @property
    def nxfilename(self):
        if self._filename is not None:
            if os.path.isabs(self._filename):
                return self._filename
            elif self._group is not None and self._group.nxfilename is not None:
                return os.path.abspath(
                    os.path.join(os.path.dirname(self._group.nxfilename),
                                 self._filename))
            else:
                return os.path.abspath(self._filename)
        elif self._group is not None:
            return self._group.nxfilename
        else:
            return None

    @property
    def nxfilepath(self):
        if self.nxclass == 'NXroot':
            return "/"
        elif isinstance(self, NXlink):
            return self.nxtarget
        elif self.nxgroup is None:
            return ""
        elif isinstance(self.nxgroup, NXroot):
            return "/" + self.nxname
        elif isinstance(self.nxgroup, NXlink):
            group_path = self.nxgroup.nxtarget
        else:
            group_path = self.nxgroup.nxfilepath
        if group_path:
            return group_path+"/"+self.nxname
        else:
            return self.nxname

    @property
    def nxfullpath(self):
        return self.nxfilename+"['"+self.nxfilepath+"']"

    @property
    def nxfilemode(self):
        if self._mode is not None:
            return self._mode
        elif self._group is not None:
            return self._group.nxfilemode
        else:
            return None

    @property
    def nxtarget(self):
        return self._target

    @property
    def attrs(self):
        if self._attrs is None:
            self._attrs = AttrDict()
        return self._attrs

    def is_plottable(self):
        return False

    def is_external(self):
        return (self.nxfilename is not None and 
                self.nxfilename != self.nxroot.nxfilename)

    def file_exists(self):
        if self.nxfilename is not None:
            return os.path.exists(self.nxfilename)
        else:
            return True

    def path_exists(self):
        if self.is_external():
            if self.file_exists():
                with self.nxfile as f:
                    return self.nxfilepath in f
            else:
                return False
        else:
            return True

    def exists(self):
        return self.file_exists() and self.path_exists()


class NXfield(NXobject):

    """
    A NeXus data field.

    This is a subclass of NXobject that contains scalar, array, or string data
    and associated NeXus attributes.

    Parameters
    ----------
    value : scalar value, Numpy array, or string
        The numerical or string value of the NXfield, which is directly
        accessible as the NXfield attribute 'nxdata'.
    name : string
        The name of the NXfield, which is directly accessible as the NXfield
        attribute 'name'. If the NXfield is initialized as the attribute of a
        parent object, the name is automatically set to the name of this
        attribute.
    dtype : string
        The data type of the NXfield value, which is directly accessible as the
        NXfield attribute 'dtype'. Valid input types correspond to standard
        Numpy data types, using names defined by the NeXus API, i.e.,
        'float32' 'float64'
        'int8' 'int16' 'int32' 'int64'
        'uint8' 'uint16' 'uint32' 'uint64'
        'char'
        If the data type is not specified, then it is determined automatically
        by the data type of the 'value' parameter.
    shape : list of ints
        The dimensions of the NXfield data, which is accessible as the NXfield
        attribute 'shape'. This corresponds to the shape of the Numpy array.
        Scalars (numeric or string) are stored as Numpy zero-rank arrays,
        for which shape=[].
    attrs : dict
        A dictionary containing NXfield attributes. The dictionary values should
        all have class NXattr.
    file : filename
        The file from which the NXfield has been read.
    path : string
        The path to this object with respect to the root of the NeXus tree,
        using the convention for unix file paths.
    group : NXgroup or subclass of NXgroup
        The parent NeXus object. If the NXfield is initialized as the attribute
        of a parent group, this attribute is automatically set to the parent 
        group.

    Attributes
    ----------
    nxclass : 'NXfield'
        The class of the NXobject.
    nxname : string
        The name of the NXfield. Since it is possible to reference the same
        Python object multiple times, this is not necessarily the same as the
        object name. However, if the field is part of a NeXus tree, this will
        be the attribute name within the tree.
    nxgroup : NXgroup
        The parent group containing this field within a NeXus tree. If the
        field is not part of any NeXus tree, it will be set to None.
    dtype : string or Numpy dtype
        The data type of the NXfield value. If the NXfield has been initialized
        but the data values have not been read in or defined, this is a string.
        Otherwise, it is set to the equivalent Numpy dtype.
    shape : list or tuple of ints
        The dimensions of the NXfield data. If the NXfield has been initialized
        but the data values have not been read in or defined, this is a list of
        ints. Otherwise, it is set to the equivalent Numpy shape, which is a
        tuple. Scalars (numeric or string) are stored as Numpy zero-rank arrays,
        for which shape=().
    attrs : dict
        A dictionary of all the NeXus attributes associated with the field.
        These are objects with class NXattr.
    nxdata : scalar, Numpy array or string
        The data value of the NXfield. This is normally initialized using the
        'value' parameter (see above). If the NeXus data is contained
        in a file and the size of the NXfield array is too large to be stored
        in memory, the value is not read in until this attribute is directly
        accessed. Even then, if there is insufficient memory, a value of None
        will be returned. In this case, the NXfield array should be read as a
        series of smaller slabs using 'get'.
    nxdata_as('units') : scalar value or Numpy array
        If the NXfield 'units' attribute has been set, the data values, stored
        in 'nxdata', are returned after conversion to the specified units.
    nxpath : string
        The path to this object with respect to the root of the NeXus tree. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.
    nxroot : NXgroup
        The root object of the NeXus tree containing this object. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.

    **NeXus Attributes**

    NeXus attributes are stored in the 'attrs' dictionary of the NXfield, but
    can usually be assigned or referenced as if they are Python attributes, as
    long as the attribute name is not the same as one of those listed above.
    This is to simplify typing in an interactive session and should not cause
    any problems because there is no name clash with attributes so far defined
    within the NeXus standard. When writing modules, it is recommended that the
    attributes always be referenced using the 'attrs' dictionary if there is
    any doubt.

    1) Assigning a NeXus attribute

       In the example below, after assigning the NXfield, the following three
       NeXus attribute assignments are all equivalent:

        >>> entry.sample.temperature = NXfield(40.0)
        >>> entry.sample.temperature.attrs['units'] = 'K'
        >>> entry.sample.temperature.units = NXattr('K')
        >>> entry.sample.temperature.units = 'K'

    2) Referencing a NeXus attribute

       If the name of the NeXus attribute is not the same as any of the Python
       attributes listed above, or one of the methods listed below, or any of the
       attributes defined for Numpy arrays, they can be referenced as if they were
       a Python attribute of the NXfield. However, it is only possible to reference
       attributes with one of the proscribed names using the 'attrs' dictionary.

        >>> entry.sample.temperature.tree = 10.0
        >>> entry.sample.temperature.tree
        temperature = 40.0
          @tree = 10.0
          @units = K
        >>> entry.sample.temperature.attrs['tree']
        NXattr(10.0)

    **Numerical Operations on NXfields**

    NXfields usually consist of arrays of numeric data with associated
    meta-data, the NeXus attributes. The exception is when they contain
    character strings. This makes them similar to Numpy arrays, and this module
    allows the use of NXfields in numerical operations in the same way as Numpy
    ndarrays. NXfields are technically not a sub-class of the ndarray class, but
    most Numpy operations work on NXfields, returning either another NXfield or,
    in some cases, an ndarray that can easily be converted to an NXfield.

        >>> x = NXfield((1.0,2.0,3.0,4.0))
        >>> print x+1
        [ 2.  3.  4.  5.]
        >>> print 2*x
        [ 2.  4.  6.  8.]
        >>> print x/2
        [ 0.5  1.   1.5  2. ]
        >>> print x**2
        [  1.   4.   9.  16.]
        >>> print x.reshape((2,2))
        [[ 1.  2.]
         [ 3.  4.]]
        >>> y = NXfield((0.5,1.5,2.5,3.5))
        >>> x+y
        NXfield(name=x,value=[ 1.5  3.5  5.5  7.5])
        >>> x*y
        NXfield(name=x,value=[  0.5   3.    7.5  14. ])
        >>> (x+y).shape
        (4,)
        >>> (x+y).dtype
        dtype('float64')

    All these operations return valid NXfield objects containing the same
    attributes as the first NXobject in the expression. The 'reshape' and
    'transpose' methods also return NXfield objects.

    It is possible to use the standard slice syntax.

        >>> x=NXfield(np.linspace(0,10,11))
        >>> x
        NXfield([  0.   1.   2. ...,   8.   9.  10.])
        >>> x[2:5]
        NXfield([ 2.  3.  4.])

    In addition, it is possible to use floating point numbers as the slice
    indices. If one of the indices is not integer, both indices are used to
    extract elements in the array with values between the two index values.

        >>> x=NXfield(np.linspace(0,100.,11))
        >>> x
        NXfield([   0.   10.   20. ...,   80.   90.  100.])
        >>> x[20.:50.]
        NXfield([ 20.  30.  40.  50.])

    The standard Numpy ndarray attributes and methods will also work with
    NXfields, but will return scalars or Numpy arrays.

        >>> x.size
        4
        >>> x.sum()
        10.0
        >>> x.max()
        4.0
        >>> x.mean()
        2.5
        >>> x.var()
        1.25
        >>> x.reshape((2,2)).sum(1)
        array([ 3.,  7.])

    Finally, NXfields are cast as ndarrays for operations that require them.
    The returned value will be the same as for the equivalent ndarray
    operation, e.g.,

    >>> np.sin(x)
    array([ 0.84147098,  0.90929743,  0.14112001, -0.7568025 ])
    >>> np.sqrt(x)
    array([ 1.        ,  1.41421356,  1.73205081,  2.        ])

    Examples
    --------
    >>> x = NXfield(np.linspace(0,2*np.pi,101), units='degree')
    >>> phi = x.nxdata_as(units='radian')
    >>> y = NXfield(np.sin(phi))
    >>> # Read a Ni x Nj x Nk array one vector at a time
    >>> with root.NXentry[0].data.data as slab:
            Ni,Nj,Nk = slab.shape
            size = [1,1,Nk]
            for i in range(Ni):
                for j in range(Nj):
                    value = slab.get([i,j,0],size)

    """
    properties = ['mask', 'dtype', 'shape', 'chunks', 'compression', 'compression_opts',
                  'fillvalue', 'fletcher32', 'maxshape', 'scaleoffset', 'shuffle']

    def __init__(self, value=None, name='unknown', shape=None, dtype=None, 
                 group=None, attrs={}, **kwargs):
        self._class = 'NXfield'
        self._name = name
        self._group = group
        self._value, self._dtype, self._shape = _getvalue(value, dtype, shape)
        _size = _getsize(self._shape)
        _h5opts = {}
        _h5opts['chunks'] = kwargs.pop('chunks', True if _size>NX_MAXSIZE else None)
        _h5opts['compression'] = kwargs.pop('compression', 
                                            NX_COMPRESSION if _size>NX_MAXSIZE else None)
        _h5opts['compression_opts'] = kwargs.pop('compression_opts', None)
        _h5opts['fillvalue'] = kwargs.pop('fillvalue', None)
        _h5opts['fletcher32'] = kwargs.pop('fletcher32', None)
        _h5opts['maxshape'] = _getmaxshape(kwargs.pop('maxshape', None), self._shape)
        _h5opts['scaleoffset'] = kwargs.pop('scaleoffset', None)
        _h5opts['shuffle'] = kwargs.pop('shuffle', True if _size>NX_MAXSIZE else None)
        self._h5opts = dict((k, v) for (k, v) in _h5opts.items() if v is not None)
        attrs.update(kwargs)
        self._attrs = AttrDict(self, attrs=attrs)
        self._memfile = None
        self._uncopied_data = None
        self.set_changed()

    def __dir__(self):
        return sorted([c for c in dir(super(self.__class__, self)) 
                       if not c.startswith('_')]+list(self.attrs), 
                      key=natural_sort)

    def __repr__(self):
        if self._value is not None:
            return "NXfield(%s)" % repr(self.nxvalue)
        else:
            return "NXfield(shape=%s, dtype=%s)" % (self.shape, self.dtype)

    def __str__(self):
        if self._value is not None:
            return text(self.nxvalue)
        return ""

    def __unicode__(self):
        if self._value is not None:
            return text(self.nxvalue)
        return u""

    def __getattr__(self, name):
        """
        Enables standard numpy ndarray attributes if not otherwise defined.
        """
        if name in _npattrs:
            return getattr(self.nxdata, name)
        elif name in self.attrs:
            return self.attrs[name]
        else:
            raise AttributeError("'"+name+"' not in "+self.nxpath)

    def __setattr__(self, name, value):
        """
        Adds an attribute to the NXfield 'attrs' dictionary unless the attribute
        name starts with 'nx' or '_', or unless it is one of the standard Python
        attributes for the NXfield class.
        """
        if (name.startswith('_') or name.startswith('nx') or 
            name in self.properties):
            object.__setattr__(self, name, value)
        elif self.nxfilemode == 'r':
            raise NeXusError("NeXus file opened as readonly")
        else:
            self._attrs[name] = value
            self.set_changed()

    def __delattr__(self, name):
        """
        Deletes an attribute in the NXfield 'attrs' dictionary.
        """
        if name in self.attrs:
            del self.attrs[name]
        self.set_changed()

    def __getitem__(self, idx):
        """
        Returns a slice from the NXfield.

        In most cases, the slice values are applied to the NXfield nxdata array
        and returned within an NXfield object with the same metadata. However,
        if the array is one-dimensional and the index start and stop values
        are real, the nxdata array is returned with values between those limits.
        This is to allow axis arrays to be limited by their actual value. This
        real-space slicing should only be used on monotonically increasing (or
        decreasing) one-dimensional arrays.
        """
        idx = convert_index(idx, self)
        if self._value is None:
            if self._uncopied_data:
                result = self._get_uncopied_data(idx)
            elif self.nxfilemode:
                result = self._get_filedata(idx)
            elif self._memfile:
                result = self._get_memdata(idx)
                mask = self.mask
                if mask is not None:
                    if isinstance(mask, NXfield):
                        mask = mask[idx].nxdata
                    else:
                        mask = mask[idx]
                    if isinstance(result, np.ma.MaskedArray):
                        result = result.data
                    result = np.ma.array(result, mask=mask)
            elif self.fillvalue:
                result = np.asarray(np.empty(self.shape, dtype=self.dtype)[idx])
                result.fill(self.fillvalue)
            else:
                raise NeXusError(
                    "Data not available either in file or in memory")
        else:
            result = np.asarray(self.nxdata[idx])
        return NXfield(result, name=self.nxname, attrs=self.safe_attrs)

    def __setitem__(self, idx, value):
        """
        Assigns a slice to the NXfield.
        """
        if self.nxfilemode == 'r':
            raise NeXusError("NeXus file opened as readonly")
        idx = convert_index(idx, self)
        if value is np.ma.masked:
            self._mask_data(idx)
        else:
            if isinstance(value, np.bool_) and self.dtype != np.bool_:
                raise NeXusError(
                    "Cannot set a Boolean value to a non-Boolean data type")
            elif value is np.ma.nomask:
                value = False
            if isinstance(value, NXfield):
                value = value.nxdata
            if self._value is not None:
                self._value[idx] = value
            if self.nxfilemode == 'rw':
                self._put_filedata(value, idx)
            elif self._value is None:
                if self.size > NX_MAXSIZE:
                    self._put_memdata(value, idx)
                else:
                    self._value = np.empty(self.shape, self.dtype)
                    if self.fillvalue:
                        self._value.fill(self.fillvalue)
                    elif is_string_dtype(self.dtype):
                        self._value.fill(' ')
                    else:
                        self._value.fill(0)
                    self._value[idx] = value
        self.set_changed()

    def _str_name(self, indent=0):
        s = text(self).replace('\r\n', '\n')
        if self.dtype is not None:
            if is_string_dtype(self.dtype):
                if len(s) > 60:
                    s = s[:56] + '...'
                try:
                    s = s[:s.index('\n')]+'...'
                except ValueError:
                    pass
                if len(self) == 1:
                    s = "'" + s + "'"
            elif len(self) > 3 or '\n' in s or s == "":
                if self.shape is None:
                    dims = ''
                else:
                    dims = 'x'.join([text(n) for n in self.shape])
                s = "%s(%s)" % (self.dtype, dims)
        elif s == "":
            s = "None"
        try:
            return " " * indent + self.nxname + " = " + s
        except Exception:
            return " " * indent + self.nxname

    def _get_filedata(self, idx=()):
        with self.nxfile as f:
            result = f.readvalue(self.nxfilepath, idx=idx)
            if 'mask' in self.attrs:
                try:
                    mask = self.nxgroup[self.attrs['mask']]
                    result = np.ma.array(result, 
                                         mask=f.readvalue(mask.nxfilepath,
                                                          idx=idx))
                except KeyError:
                    pass
        return result

    def _put_filedata(self, value, idx=()):
        with self.nxfile as f:
            if isinstance(value, np.ma.MaskedArray):
                if self.mask is None:
                    self._create_mask()
                f.writevalue(self.nxpath, value.data, idx=idx)
                f.writevalue(self.mask.nxpath, value.mask, idx=idx)
            else:
                f.writevalue(self.nxpath, value, idx=idx)

    def _get_memdata(self, idx=()):
        result = self._memfile['data'][idx]
        if 'mask' in self._memfile:
            mask = self._memfile['mask'][idx]
            if mask.any():
                result = np.ma.array(result, mask=mask)
        return result
    
    def _put_memdata(self, value, idx=()):
        if self._memfile is None:
            self._create_memfile()
        if 'data' not in self._memfile:
            self._create_memdata()
        self._memfile['data'][idx] = value
        if isinstance(value, np.ma.MaskedArray):
            if 'mask' not in self._memfile:
                self._create_memmask()
            self._memfile['mask'][idx] = value.mask
    
    def _create_memfile(self):
        """
        Creates an HDF5 memory-mapped file to store the data
        """
        import tempfile
        self._memfile = h5.File(tempfile.mkstemp(suffix='.nxs')[1],
                                driver='core', backing_store=False).file

    def _create_memdata(self):
        """
        Creates an HDF5 memory-mapped dataset to store the data
        """
        if self._shape is not None and self._dtype is not None:
            if self._memfile is None:
                self._create_memfile()
            self._memfile.create_dataset('data', shape=self._shape, dtype=self._dtype, 
                                         **self._h5opts)
        else:
            raise NeXusError(
                "Cannot allocate to field before setting shape and dtype")       

    def _create_memmask(self):
        """
        Creates an HDF5 memory-mapped dataset to store the data mask
        """
        if self._shape is not None:
            if self._memfile is None:
                self._create_memfile()
            self._memfile.create_dataset('mask', shape=self._shape, dtype=np.bool,
                                         **self._h5opts)
        else:
            raise NeXusError("Cannot allocate mask before setting shape")       

    def _create_mask(self):
        """
        Create a data mask field if none exists
        """
        if self.nxgroup is not None:
            if 'mask' in self.attrs:
                mask_name = self.attrs['mask']
                if mask_name in self.nxgroup:
                    return mask_name
            mask_name = '%s_mask' % self.nxname
            self.nxgroup[mask_name] = NXfield(shape=self._shape, dtype=np.bool, 
                                              fillvalue=False)
            self.attrs['mask'] = mask_name
            return mask_name
        return None      

    def _mask_data(self, idx=()):
        """
        Add a data mask covering the specified indices
        """
        mask_name = self._create_mask()
        if mask_name:
            self.nxgroup[mask_name][idx] = True
        elif self._memfile:
            if 'mask' not in self._memfile:
                self._create_memmask()
            self._memfile['mask'][idx] = True
        if self._value is not None:
            if not isinstance(self._value, np.ma.MaskedArray):
                self._value = np.ma.array(self._value)
            self._value[idx] = np.ma.masked

    def _get_uncopied_data(self, idx=None):
        _file, _path = self._uncopied_data
        with _file as f:
            if idx:
                return f.readvalue(_path, idx=idx)
            else:
                if self.nxfilemode == 'rw':
                    f.copy(_path, self.nxpath)
                else:
                    self._create_memfile()
                    f.copy(_path, self._memfile, 'data')
                self._uncopied_data = None
                if (np.prod(self.shape) * np.dtype(self.dtype).itemsize 
                    <= NX_MEMORY*1000*1000):
                    return f.readvalue(_path)
                else:
                    return None

    def __deepcopy__(self, memo={}):
        obj = self
        dpcpy = obj.__class__()
        memo[id(self)] = dpcpy
        dpcpy._name = copy(self.nxname)
        dpcpy._dtype = copy(obj.dtype)
        dpcpy._shape = copy(obj.shape)
        dpcpy._h5opts = copy(obj._h5opts)
        dpcpy._changed = True
        dpcpy._memfile = obj._memfile
        dpcpy._uncopied_data = obj._uncopied_data
        if obj._value is not None:
            dpcpy._value = copy(obj._value)
            dpcpy._memfile = dpcpy._uncopied_data = None
        elif obj.nxfilemode:
            dpcpy._uncopied_data = (obj.nxfile, obj.nxpath)
        for k, v in obj.attrs.items():
            dpcpy.attrs[k] = copy(v)
        if 'target' in dpcpy.attrs:
            del dpcpy.attrs['target']
        dpcpy._group = None
        return dpcpy

    def __iter__(self):
        """
        Implements key iteration
        """
        try:
            return self.nxvalue.__iter__()
        except AttributeError:
            return self
            
    def __next__(self):
        """
        Implements key iteration
        """
        try:
            return self.nxvalue.__next__()
        except AttributeError:
            raise StopIteration
            
    def __contains__(self, key):
        """Implements 'k in d' test using the NXfield nxvalue."""
        return self.nxvalue.__contains__(key)

    def __len__(self):
        """
        Returns the length of the NXfield data.
        """
        try:
            return self.shape[0]
        except Exception:
            return 0

    def __nonzero__(self):
        """
        Returns False if all values are 0 or False, True otherwise.
        """
        try:
            if np.any(self.nxvalue):
                return True
            else:
                return False
        except NeXusError:
            #This usually means that there are too many values to load
            return True

    def index(self, value, max=False):
        """
        Returns the index of a one-dimensional NXfield element that is less
        than (greater than) or equal to the given value for a monotonically 
        increasing (decreasing) array.

        If max=True, then it returns the index that is greater than (less than) 
        or equal to the value for a monotonically increasing (decreasing) array.
        
        >>> field
        NXfield([ 0.   0.1  0.2 ...,  0.8  0.9  1. ])
        >>> field.index(0.1)
        1
        >>> field.index(0.11)
        1
        >>> field.index(0.11, max=True)
        2
        >>> reverse_field
        NXfield([ 1.   0.9  0.8 ...,  0.2  0.1  0. ])
        >>> reverse_field.index(0.89)
        1
        >>> reverse_field.index(0.89, max=True)
        2

        The value is considered to be equal to an NXfield element's value if it
        differs by less than 1% of the step size to the neighboring element. 
        
        This raises a NeXusError if the array is not one-dimensional.
        """
        if self.ndim != 1:
            raise NeXusError(
                "NXfield must be one-dimensional to use the index function")
        if self.nxdata[-1] < self.nxdata[0]:
            flipped = True
        else:
            flipped = False
        if max:
            if flipped:
                idx = np.max(len(self.nxdata) - 
                             len(self.nxdata[self.nxdata<value])-1,0)
            else:
                idx = np.max(len(self.nxdata) - 
                             len(self.nxdata[self.nxdata>value])-1,0)
            try:
                diff = value - self.nxdata[idx]
                step = self.nxdata[idx+1] - self.nxdata[idx]
                if abs(diff/step) > 0.01:
                    idx = idx + 1
            except IndexError:
                pass
        else:
            if flipped:
                idx = len(self.nxdata[self.nxdata>value])
            else:
                idx = len(self.nxdata[self.nxdata<value])
            try:
                diff = value - self.nxdata[idx-1]
                step = self.nxdata[idx] - self.nxdata[idx-1]
                if abs(diff/step) < 0.99:
                    idx = idx - 1
            except IndexError:
                pass
        return int(np.clip(idx, 0, len(self.nxdata)-1))

    def __array__(self):
        """
        Casts the NXfield as an array when it is expected by numpy
        """
        return np.asarray(self.nxdata)

    def __array_wrap__(self, value):
        """
        Transforms the array resulting from a ufunc to an NXfield
        """
        return NXfield(value, name=self.nxname)

    def __int__(self):
        """
        Casts a scalar field as an integer
        """
        return int(self.nxvalue)

    def __long__(self):
        """
        Casts a scalar field as a long integer

        The use of the 'long' function is not valid in Python 3 and 
        no longer useful in Python 2
        """
        return int(self.nxvalue)

    def __float__(self):
        """
        Casts a scalar field as floating point number
        """
        return float(self.nxvalue)

    def __complex__(self):
        """
        Casts a scalar field as a complex number
        """
        return complex(self.nxvalue)

    def __neg__(self):
        """
        Returns the negative value of a scalar field
        """
        return -self.nxvalue

    def __abs__(self):
        """
        Returns the absolute value of a scalar field
        """
        return abs(self.nxvalue)

    def __eq__(self, other):
        """
        Returns true if the values of the NXfield are the same.
        """
        if id(self) == id(other):
            return True
        elif isinstance(other, NXfield):
            if (isinstance(self.nxvalue, np.ndarray) and
                   isinstance(other.nxvalue, np.ndarray)):
                try:
                    return np.array_equal(self, other)
                except ValueError:
                    return False
            else:
                return self.nxvalue == other.nxvalue
        else:
            return self.nxvalue == other

    def __ne__(self, other):
        """
        Returns true if the values of the NXfield are not the same.
        """
        if isinstance(other, NXfield):
            if (isinstance(self.nxvalue, np.ndarray) and
                   isinstance(other.nxvalue, np.ndarray)):
                try:
                    return not np.array_equal(self, other)
                except ValueError:
                    return True
            else:
                return self.nxvalue != other.nxvalue
        else:
            return self.nxvalue != other

    def __lt__(self, other):
        """
        Returns true if self.nxvalue < other[.nxvalue]
        """
        if isinstance(other, NXfield):
            return self.nxvalue < other.nxvalue
        else:
            return self.nxvalue < other

    def __le__(self, other):
        """
        Returns true if self.nxvalue <= other[.nxvalue]
        """
        if isinstance(other, NXfield):
            return self.nxvalue <= other.nxvalue
        else:
            return self.nxvalue <= other

    def __gt__(self, other):
        """
        Returns true if self.nxvalue > other[.nxvalue]
        """
        if isinstance(other, NXfield):
            return self.nxvalue > other.nxvalue
        else:
            return self.nxvalue > other

    def __ge__(self, other):
        """
        Returns true if self.nxvalue >= other[.nxvalue]
        """
        if isinstance(other, NXfield):
            return self.nxvalue >= other.nxvalue
        else:
            return self.nxvalue >= other

    def __add__(self, other):
        """
        Returns the sum of the NXfield and another NXfield or number.
        """
        if isinstance(other, NXfield):
            return NXfield(value=self.nxdata+other.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=self.nxdata+other, name=self.nxname,
                           attrs=self.safe_attrs)
 
    def __radd__(self, other):
        """
        Returns the sum of the NXfield and another NXfield or number.

        This variant makes __add__ commutative.
        """
        return self.__add__(other)

    def __sub__(self, other):
        """
        Returns the NXfield with the subtraction of another NXfield or number.
        """
        if isinstance(other, NXfield):
            return NXfield(value=self.nxdata-other.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=self.nxdata-other, name=self.nxname,
                           attrs=self.safe_attrs)

    def __rsub__(self, other):
        """
        Returns the NXfield after subtracting from another number.
        """
        if isinstance(other, NXfield):
            return NXfield(value=other.nxdata-self.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=other-self.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)

    def __mul__(self, other):
        """
        Returns the product of the NXfield and another NXfield or number.
        """
        if isinstance(other, NXfield):
            return NXfield(value=self.nxdata*other.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=self.nxdata*other, name=self.nxname,
                           attrs=self.safe_attrs)

    def __rmul__(self, other):
        """
        Returns the product of the NXfield and another NXfield or number.

        This variant makes __mul__ commutative.
        """
        return self.__mul__(other)

    def __truediv__(self, other):
        """
        Returns the NXfield divided by another NXfield or number.
        """
        if isinstance(other, NXfield):
            return NXfield(value=self.nxdata/other.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=self.nxdata/other, name=self.nxname,
                           attrs=self.safe_attrs)

    __div__ = __truediv__

    def __rtruediv__(self, other):
        """
        Returns the inverse of the NXfield divided by another NXfield or number.
        """
        if isinstance(other, NXfield):
            return NXfield(value=other.nxdata/self.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=other/self.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)

    __rdiv__ = __rtruediv__

    def __pow__(self, power):
        """
        Returns the NXfield raised to the specified power.
        """
        return NXfield(value=pow(self.nxdata,power), name=self.nxname,
                       attrs=self.safe_attrs)

    def min(self, axis=None):
        """
        Returns the minimum value of the array ignoring NaNs
        """
        return np.nanmin(self.nxdata[self.nxdata>-np.inf], axis) 

    def max(self, axis=None):
        """
        Returns the maximum value of the array ignoring NaNs
        """
        return np.nanmax(self.nxdata[self.nxdata<np.inf], axis) 

    def sum(self, axis=None):
        """
        Returns the sum of the NXfield. The sum is over a single axis or a tuple 
        of axes using the Numpy sum method.
        """
        return NXfield(np.sum(self.nxdata, axis), name=self.nxname, 
                       attrs=self.safe_attrs)

    def average(self, axis=None):
        """
        Returns the average of the NXfield. The sum is over a single axis or a 
        tuple of axes using the Numpy average method. 
        """
        return NXfield(np.average(self.nxdata, axis), name=self.nxname, 
                       attrs=self.safe_attrs)

    def reshape(self, shape):
        """
        Returns an NXfield with the specified shape.
        """
        return NXfield(value=self.nxdata, name=self.nxname, shape=shape,
                       attrs=self.safe_attrs)

    def transpose(self):
        """
        Returns an NXfield containing the transpose of the data array.
        """
        value = self.nxdata.transpose()
        return NXfield(value=value, name=self.nxname,
                       shape=value.shape, attrs=self.safe_attrs)

    @property
    def T(self):
        return self.transpose()

    def centers(self):
        """
        Returns an NXfield with the centers of a single axis
        assuming it contains bin boundaries.
        """
        return NXfield((self.nxdata[:-1]+self.nxdata[1:])/2,
                        name=self.nxname, attrs=self.safe_attrs)

    def boundaries(self):
        """
        Returns an NXfield with the boundaries of a single axis
        assuming it contains bin centers.
        """
        ax = self.nxdata
        start = ax[0] - (ax[1] - ax[0])/2
        end = ax[-1] + (ax[-1] - ax[-2])/2
        return NXfield(np.concatenate((np.atleast_1d(start), 
                                       (ax[:-1] + ax[1:])/2, 
                                       np.atleast_1d(end))),
                       name=self.nxname, attrs=self.safe_attrs)

    def add(self, data, offset):
        """
        Adds a slab into the data array.
        """
        idx = tuple(slice(i,i+j) for i,j in zip(offset,data.shape))
        if isinstance(data, NXfield):
            self[idx] += data.nxdata.astype(self.dtype)
        else:
            self[idx] += data.astype(self.dtype)

    def convert(self, units=""):
        """
        Returns the data in the requested units.
        """
        try:
            import units
        except ImportError:
            raise NeXusError("No conversion utility available")
        if self._value is not None:
            return self._converter(self.nxvalue, units)
        else:
            return None

    def walk(self):
        yield self

    def replace(self, value):
        """
        Replace the value of a field.

        If the size or dtype of the field differs from an existing field within
        a saved group, the original field will be deleted and replaced by the 
        newone. Otherwise, the field values are updated.
        """
        group = self.nxgroup
        if group is None:
            raise NeXusError("The field must be a member of a group")
        if isinstance(value, NXfield):
            del group[self.nxname]
            group[self.nxname] = value
        elif is_text(value):
            if self.dtype == string_dtype:
                self.nxdata = value
                group.update()
            else:
                del group[self.nxname]
                group[self.nxname] = NXfield(value, attrs=self.attrs)
        else:
            value = np.asarray(value)
            if value.shape == self.shape and value.dtype == self.dtype:
                self.nxdata = value
                group.update()
            else:
                del group[self.nxname]
                group[self.nxname] = NXfield(value, attrs=self.attrs)

    @property
    def nxaxes(self):
        """
        Returns a list of NXfields containing axes.

        If the NXfield does not have the 'axes' attribute but is defined as
        the signal in its parent group, a list of the parent group's axes will
        be returned. 
        """
        def invalid_axis(axis):
            return axis.size != self.shape[i] and axis.size != self.shape[i]+1
        def empty_axis(i):
            return NXfield(np.arange(self.shape[i]), name='Axis%s'%i)
        def plot_axis(axis):
            return NXfield(axis.nxvalue, name=axis.nxname, attrs=axis.attrs) 
        if self.nxgroup:
            if 'axes' in self.attrs:
                axis_names = _readaxes(self.attrs['axes'])
            elif 'axes' in self.nxgroup.attrs:
                axis_names = _readaxes(self.nxgroup.attrs['axes'])
            else:
                axis_names = ['.'] * self.plot_rank
            if len(axis_names) > self.plot_rank:
                axis_names = axis_names[:self.plot_rank]
            axes = []
            for i, axis_name in enumerate(axis_names):
                axis_name = axis_name.strip()
                if (axis_name not in self.nxgroup or  
                    invalid_axis(self.nxgroup[axis_name])):
                    axes.append(empty_axis(i))
                else:
                    axes.append(plot_axis(self.nxgroup[axis_name]))
            return axes
        else:
            return [empty_axis(i) for i in range(self.plot_rank)]

    def valid_axes(self, axes):
        """Return True if the axes are consistent with the field.
        
        It checks that all the axes are one-dimensional, and that the size of
        each axis is equal to or one greater than the field dimension.
        
        Parameters
        ----------
        axes : list
            List of NXfields
        
        Note
        ----
        The function removes scalar axes before the check even though these are 
        returned by the nxaxes property. That is because ndim is 0 for scalars.
        They are automatically removed when plotting so this does not 
        invalidate the check.
        """
        if not is_iterable(axes):
            axes = [axes]
        plot_axes = [axis for axis in axes if axis.size > 1]
        axis_shape = [axis.size for axis in plot_axes]
        if (all(axis.ndim == 1 for axis in plot_axes) and 
            len([x for x,y in zip(self.plot_shape, axis_shape) 
                 if x==y or x==y-1]) == self.plot_rank):
            return True
        else:
            return False

    @property
    def nxvalue(self):
        """Returns the NXfield value.
        
        This is the value stored in the NeXus file, with the following
        exceptions.
            1) Size-1 arrays are returned as scalars.
            2) String or byte arrays are returns as a list of strings.

        Note
        ----
        If unmodified values are required, use the 'nxdata' property.
        """
        _value = self.nxdata
        if _value is None:
            return None
        elif (self.dtype is not None and
            (self.dtype.type == np.string_ or self.dtype.type == np.str_ or 
             self.dtype == string_dtype)):
            if self.shape == ():
                return text(_value)
            elif self.shape == (1,):
                return text(_value[0])
            else:
                return [text(value) for value in _value[()]]
        elif self.shape == (1,):
            return _value.item()
        else:
            return _value

    @property
    def nxdata(self):
        """Returns the NXfield data if it is not larger than NX_MEMORY."""
        if self._value is None:
            if self.dtype is None or self.shape is None:
                return None
            if (np.prod(self.shape) * np.dtype(self.dtype).itemsize 
                <= NX_MEMORY*1000*1000):
                try:
                    if self.nxfilemode:
                        self._value = self._get_filedata()
                    elif self._uncopied_data:
                        self._value = self._get_uncopied_data()
                    if self._memfile:
                        self._value = self._get_memdata()
                except Exception:
                    raise NeXusError("Cannot read data for '%s'" % self.nxname)
                if self._value is not None:
                    self._value.shape = self.shape
            else:
                raise NeXusError(
                    "Use slabs to access data larger than NX_MEMORY=%s MB" 
                    % NX_MEMORY)
        if self.mask is not None:
            try:
                if isinstance(self.mask, NXfield):
                    mask = self.mask.nxdata
                    if isinstance(self._value, np.ma.MaskedArray):
                        self._value.mask = mask
                    else:
                        self._value = np.ma.array(self._value, mask=mask)
            except Exception:
                pass
        return self._value

    @nxdata.setter
    def nxdata(self, value):
        if self.nxfilemode == 'r':
            raise NeXusError("NeXus file is locked")
        else:
            self._value, self._dtype, self._shape = _getvalue(
                value, self._dtype, self._shape)
            if self._memfile:
                self._put_memdata(self._value)

    @property
    def nxtitle(self):
        """
        Returns the title as a string.

        If there is no title attribute in the parent group, the group's path is 
        returned.
        """
        root = self.nxroot
        if root.nxname != '' and root.nxname != 'root':
            return (root.nxname + '/' + self.nxpath.lstrip('/')).rstrip('/')
        else:
            fname = self.nxfilename
            if fname is not None:
                return fname + ':' + self.nxpath
            else:
                return self.nxpath

    @property
    def mask(self):
        """
        Returns the NXfield's mask as an array.

        Only works if the NXfield is in a group and has the 'mask' attribute set
        or if the NXfield array is defined as a masked array.
        """
        if 'mask' in self.attrs:
            if self.nxgroup and self.attrs['mask'] in self.nxgroup:
                return self.nxgroup[self.attrs['mask']]
        if self._value is None and self._memfile:
            if 'mask' in self._memfile:
                return self._memfile['mask']      
        if self._value is not None and isinstance(self._value, 
                                                  np.ma.MaskedArray):
            return self._value.mask
        return None

    @mask.setter
    def mask(self, value):
        if self.nxfilemode == 'r':
            raise NeXusError("NeXus file is locked")
        if 'mask' in self.attrs:
            if self.nxgroup:
                mask_name = self.attrs['mask']
                if mask_name in self.nxgroup:
                    self.nxgroup[mask_name][()] = value
            else:
                del self.attrs['mask']
        elif self._value is None:
            if self._memfile:
                if 'mask' not in self._memfile:
                    self._create_memmask()
                self._memfile['mask'][()] = value
        if self._value is not None:
            if isinstance(self._value, np.ma.MaskedArray):
                self._value.mask = value
            else:
                self._value = np.ma.array(self._value, mask=value)

    def resize(self, shape, axis=None):
        if axis is not None:
            if not (axis >=0 and axis < self.ndim):
                raise NeXusError("Invalid axis (0 to %s allowed)" % (self.ndim-1))
            try:
                newlen = int(shape)
            except TypeError:
                raise NeXusError("Argument must be a single integer if axis is specified")
            shape = list(self._shape)
            shape[axis] = newlen
        if self.checkshape(shape):
            if self.nxfilemode:
                with self.nxfile as f:
                    f[self.nxpath].shape = shape
                self._value = None
            elif self._memfile:
                self._memfile['data'].shape = shape
                self._value = None
        else:
            raise NeXusError("Shape incompatible with current NXfield")
        self._shape = shape
        if self._value is not None:
            self._value.resize(self._shape, refcheck=False)

    def checkshape(self, shape):
        _maxshape = self.maxshape
        if _maxshape and not _checkshape(shape, _maxshape):
            return False
        elif self.nxfilemode or self._memfile:
            return _checkshape(self._shape, shape)
        else:
            return True

    @property
    def shape(self):
        try:
            return _getshape(self._shape)
        except TypeError:
            return ()

    @shape.setter
    def shape(self, value):
        self.resize(value)

    @property
    def dtype(self):
        return self._dtype

    @dtype.setter
    def dtype(self, value):
        if self.nxfilemode:
            raise NeXusError(
                "Cannot change the dtype of a field already stored in a file")
        elif self._memfile:
            raise NeXusError(
                "Cannot change the dtype of a field already in core memory")
        self._dtype = _getdtype(value)
        if self._value is not None:
            self._value = np.asarray(self._value, dtype=self._dtype)

    def get_h5opt(self, name):
        if self.nxfilemode:
            with self.nxfile as f:
                self._h5opts[name] = getattr(f[self.nxfilepath], name)
        elif self._memfile:
            self._h5opts[name] = getattr(self._memfile['data'], name)
        if name in self._h5opts:
            return self._h5opts[name]
        else:
            return None

    def set_h5opt(self, name, value):
        if self.nxfilemode:
            raise NeXusError(
            "Cannot change the %s of a field already stored in a file" % name)
        elif self._memfile:
            raise NeXusError(
            "Cannot change the %s of a field already in core memory" % name)
        if value is not None:
            self._h5opts[name] = value
        
    @property
    def compression(self):
        return self.get_h5opt('compression')

    @compression.setter
    def compression(self, value):
        self.set_h5opt('compression', value)
        
    @property
    def compression_opts(self):
        return self.get_h5opt('compression_opts')

    @compression_opts.setter
    def compression_opts(self, value):
        self.set_h5opt('compression_opts', value)
        
    @property
    def fillvalue(self):
        return self.get_h5opt('fillvalue')

    @fillvalue.setter
    def fillvalue(self, value):
        self.set_h5opt('fillvalue', value)

    @property
    def fletcher32(self):
        return self.get_h5opt('fletcher32')

    @fletcher32.setter
    def fletcher32(self, value):
        self.set_h5opt('fletcher32', value)
        
    @property
    def chunks(self):
        return self.get_h5opt('chunks')

    @chunks.setter
    def chunks(self, value):
        if is_iterable(value) and len(value) != self.ndim:
            raise NeXusError(
                "Number of chunks does not match the no. of array dimensions")
        self.set_h5opt('chunks', value)

    @property
    def maxshape(self):
        return self.get_h5opt('maxshape')

    @maxshape.setter
    def maxshape(self, value):
        self.set_h5opt('maxshape', _getmaxshape(value, self.shape))

    @property
    def scaleoffset(self):
        return self.get_h5opt('scaleoffset')

    @scaleoffset.setter
    def scaleoffset(self, value):
        self.set_h5opt('scaleoffset', value)
        
    @property
    def shuffle(self):
        return self.get_h5opt('shuffle')

    @shuffle.setter
    def shuffle(self, value):
        self.set_h5opt('shuffle', value)
        
    @property
    def ndim(self):
        try:
            return len(self.shape)
        except TypeError:
            return 0

    @property
    def size(self):
        return int(np.prod(self.shape))

    @property
    def safe_attrs(self):
        return {key: self.attrs[key] for key in self.attrs 
                if (key != 'target' and key != 'signal' and key != 'axes')}

    @property
    def reversed(self):
        if self.ndim == 1 and self.nxdata[-1] < self.nxdata[0]:
            return True
        else:
            return False

    @property
    def plot_shape(self):
        try:  
            _shape = list(self.shape)
            while 1 in _shape:
                _shape.remove(1)
            return tuple(_shape)
        except Exception:
            return ()

    @property
    def plot_rank(self):
        return len(self.plot_shape)

    def is_plottable(self):
        if self.plot_rank > 0:
            return True
        else:
            return False

    def plot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
             vmin=None, vmax=None, **kwargs):
        """
        Plot data if the signal attribute is defined.

        The format argument is used to set the color and type of the
        markers or lines for one-dimensional plots, using the standard 
        Mtplotlib syntax. The default is set to blue circles. All 
        keyword arguments accepted by matplotlib.pyplot.plot can be
        used to customize the plot.
        
        In addition to the matplotlib keyword arguments, the following
        are defined::
        
            log = True     - plot the intensity on a log scale
            logy = True    - plot the y-axis on a log scale
            logx = True    - plot the x-axis on a log scale
            over = True    - plot on the current figure
            image = True   - plot as an RGB(A) image

        Raises NeXusError if the data could not be plotted.
        """
        if not self.exists():
            raise NeXusError("'%s' does not exist" % 
                             os.path.abspath(self.nxfilename))

        try:
            from __main__ import plotview
            if plotview is None:
                raise ImportError
        except ImportError:
            from .plot import plotview

        if self.is_plottable():
            data = NXdata(self, self.nxaxes, title=self.nxtitle)
            if self.nxroot.nxclass == "NXroot":
                signal_path = self.nxroot.nxname + self.nxpath
            else:
                signal_path = self.nxpath
            data.nxsignal.attrs['signal_path'] = signal_path
            plotview.plot(data, fmt, xmin=None, xmax=None, ymin=None, ymax=None,
                          vmin=None, vmax=None, **kwargs)
        else:
            raise NeXusError("NXfield not plottable")
    
    def oplot(self, fmt='', **kwargs):
        """
        Plots the data contained within the group over the current figure.
        """
        self.plot(fmt=fmt, over=True, **kwargs)

    def logplot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
                vmin=None, vmax=None, **kwargs):
        """
        Plots the data intensity contained within the group on a log scale.
        """
        self.plot(fmt=fmt, log=True,
                  xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                  vmin=vmin, vmax=vmax, **kwargs)

    def implot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
                vmin=None, vmax=None, **kwargs):
        """
        Plots the data intensity as an RGB(A) image.
        """
        if self.plot_rank > 2 and (self.shape[-1] == 3 or self.shape[-1] == 4):
            self.plot(fmt=fmt, image=True,
                      xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                      vmin=vmin, vmax=vmax, **kwargs)
        else:
            raise NeXusError("Invalid shape for RGB(A) image")


SDS = NXfield # For backward compatibility


class NXgroup(NXobject):

    """
    A NeXus group object.

    This is a subclass of NXobject and is the base class for the specific
    NeXus group classes, e.g., NXentry, NXsample, NXdata.

    **Parameters**

    The NXgroup parameters consist of a list of positional and/or keyword
    arguments.

    Positional Arguments: 
        These must be valid NeXus objects, either an NXfield or a NeXus group. 
        These are added without modification as children of this group.

    Keyword Arguments: 
        Apart from a list of special keywords shown below, keyword arguments are
        used to add children to the group using the keywords as attribute names. 
        The values can either be valid NXfields or NXgroups, in which case the 
        'name' attribute is changed to the keyword, or they can be numerical or 
        string data, which are converted to NXfield objects.

    Special Keyword Arguments:

        name : string
            The name of the NXgroup, which is directly accessible as the NXgroup
            attribute 'name'. If the NXgroup is initialized as the attribute of
            a parent group, the name is automatically set to the name of this
            attribute. If 'nxclass' is specified and has the usual prefix 'NX',
            the default name is the class name without this prefix.
        nxclass : string
            The class of the NXgroup.
        entries : dict
            A dictionary containing a list of group entries. This is an
            alternative way of adding group entries to the use of keyword
            arguments.
        file : filename
            The file from which the NXfield has been read.
        path : string
            The path to this object with respect to the root of the NeXus tree,
            using the convention for unix file paths.
        group : NXobject (NXgroup or subclass of NXgroup)
            The parent NeXus group, which is accessible as the group attribute
            'group'. If the group is initialized as the attribute of
            a parent group, this is set to the parent group.

    **Python Attributes**

    nxclass : string
        The class of the NXobject.
    nxname : string
        The name of the NXfield.
    entries : dictionary
        A dictionary of all the NeXus objects contained within an NXgroup.
    attrs : dictionary
        A dictionary of all the NeXus attributes, i.e., attribute with class 
        NXattr.
    entries : dictionary
        A dictionary of all the NeXus objects contained within the group.
    attrs : dictionary
        A dictionary of all the group's NeXus attributes, which all have the
        class NXattr.
    nxpath : string
        The path to this object with respect to the root of the NeXus tree. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.
    nxroot : NXgroup
        The root object of the NeXus tree containing this object. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.

    **NeXus Group Entries**

    Just as in a NeXus file, NeXus groups can contain either data or other
    groups, represented by NXfield and NXgroup objects respectively. To
    distinguish them from regular Python attributes, all NeXus objects are
    stored in the 'entries' dictionary of the NXgroup. However, they can usually
    be assigned or referenced as if they are Python attributes, i.e., using the
    dictionary name directly as the group attribute name, as long as this name
    is not the same as one of the Python attributes defined above or as one of
    the NXfield Python attributes.

    1) Assigning a NeXus object to a NeXus group

        In the example below, after assigning the NXgroup, the following three
        NeXus object assignments to entry.sample are all equivalent:

        >>> entry.sample = NXsample()
        >>> entry.sample['temperature'] = NXfield(40.0)
        >>> entry.sample.temperature = NXfield(40.0)
        >>> entry.sample.temperature = 40.0
        >>> entry.sample.temperature
        NXfield(40.0)

        If the assigned value is not a valid NXobject, then it is cast as an NXfield
        with a type determined from the Python data type.

        >>> entry.sample.temperature = 40.0
        >>> entry.sample.temperature
        NXfield(40.0)
        >>> entry.data.data.x=np.linspace(0,10,11).astype('float32')
        >>> entry.data.data.x
        NXfield([  0.   1.   2. ...,   8.   9.  10.])

    2) Referencing a NeXus object in a NeXus group

        If the name of the NeXus object is not the same as any of the Python
        attributes listed above, or the methods listed below, they can be referenced
        as if they were a Python attribute of the NXgroup. However, it is only possible
        to reference attributes with one of the proscribed names using the group
        dictionary, i.e.,

        >>> entry.sample.tree = 100.0
        >>> print entry.sample.tree
        sample:NXsample
          tree = 100.0
        >>> entry.sample['tree']
        NXfield(100.0)

        For this reason, it is recommended to use the group dictionary to reference
        all group objects within Python scripts.

    **NeXus Attributes**

    NeXus attributes are not currently used much with NXgroups, except for the
    root group, which has a number of global attributes to store the file name,
    file creation time, and NeXus and HDF version numbers. However, the
    mechanism described for NXfields works here as well. All NeXus attributes
    are stored in the 'attrs' dictionary of the NXgroup, but can be referenced
    as if they are Python attributes as long as there is no name clash.

        >>> entry.sample.temperature = 40.0
        >>> entry.sample.attrs['tree'] = 10.0
        >>> print entry.sample.tree
        sample:NXsample
          @tree = 10.0
          temperature = 40.0
        >>> entry.sample.attrs['tree']
        NXattr(10.0)

    **Methods**

    insert(self, NXobject, name='unknown'):
        Insert a valid NXobject (NXfield or NXgroup) into the group.

        If NXobject has a 'name' attribute and the 'name' keyword is not given,
        then the object is inserted with the NXobject name.

    makelink(self, NXobject):
        Add the NXobject to the group entries as a link (NXlink).

    dir(self, attrs=False, recursive=False):
        Print the group directory.

        The directory is a list of NeXus objects within this group, either NeXus
        groups or NXfield data. If 'attrs' is True, NXfield attributes are
        displayed. If 'recursive' is True, the contents of child groups are also
        displayed.

    tree:
        Returns the group tree.

        It invokes the 'dir' method with both 'attrs' and 'recursive'
        set to True.

    save(self, filename, format='w5')
        Save the NeXus group into a file

        The object is wrapped in an NXroot group (with name 'root') and an
        NXentry group (with name 'entry'), if necessary, in order to produce
        a valid NeXus file.

    **Examples**

    >>> x = NXfield(np.linspace(0,2*np.pi,101), units='degree')
    >>> entry = NXgroup(x, name='entry', nxclass='NXentry')
    >>> entry.sample = NXgroup(temperature=NXfield(40.0,units='K'),
                               nxclass='NXsample')
    >>> print entry.sample.tree
    sample:NXsample
      temperature = 40.0
        @units = K

    Note: All the currently defined NeXus classes are defined as subclasses of 
    the NXgroup class. It is recommended that these are used directly, so that 
    the above examples become:

    >>> entry = NXentry(x)
    >>> entry.sample = NXsample(temperature=NXfield(40.0,units='K'))

    or

    >>> entry.sample.temperature = 40.0
    >>> entry.sample.temperature.units='K'

    """
    _class = "NXgroup"

    def __init__(self, *args, **kwargs):
        self._entries = {}
        if "name" in kwargs:
            self._name = kwargs["name"]
            del kwargs["name"]
        if "entries" in kwargs:
            for k,v in kwargs["entries"].items():
                self._entries[k] = deepcopy(v)
            del kwargs["entries"]
        if "new_entries" in kwargs:
            for k,v in kwargs["new_entries"].items():
                self._entries[k] = v
            del kwargs["new_entries"]            
        if "attrs" in kwargs:
            self._attrs = AttrDict(self, attrs=kwargs["attrs"])
            del kwargs["attrs"]
        else:
            self._attrs = AttrDict(self)
        if "nxclass" in kwargs:
            self._class = kwargs["nxclass"]
            del kwargs["nxclass"]
        if "group" in kwargs:
            self._group = kwargs["group"]
            del kwargs["group"]
        for k,v in kwargs.items():
            try:
                self[k] = v
            except AttributeError:
                raise NeXusError(
                    "Keyword arguments must be valid NXobjects")
        if self.nxclass.startswith("NX"):
            if self.nxname == "unknown" or self.nxname == "": 
                self._name = self.nxclass[2:]
            try: # If one exists, set the class to a valid NXgroup subclass
                self.__class__ = _getclass(self._class)
            except Exception:
                pass
        for arg in args:
            try:
                self[arg.nxname] = arg
            except AttributeError:
                raise NeXusError(
                    "Non-keyword arguments must be valid NXobjects")
        self.set_changed()

    def __dir__(self):
        return sorted([c for c in dir(super(self.__class__, self))
                       if not c.startswith('_')]+list(self)+list(self.attrs), 
                      key=natural_sort)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.nxname)

    def __hash__(self):
        return id(self)

    def __getattr__(self, name):
        """
        Provides direct access to groups via nxclass name.
        """
        if name.startswith(u'NX'):
            return self.component(name)
        elif name in self.entries:
            return self.entries[name]
        elif name in self.attrs:
            return self.attrs[name]
        raise NeXusError("'"+name+"' not in "+self.nxpath)

    def __setattr__(self, name, value):
        """
        Sets an attribute as an object or regular Python attribute.

        It is assumed that attributes starting with 'nx' or '_' are regular
        Python attributes. All other attributes are converted to valid 
        NXobjects, with class NXfield, NXgroup, or a sub-class of NXgroup, 
        depending on the assigned value.

        The internal value of the attribute name, i.e., 'name', is set to the
        attribute name used in the assignment.  The parent group of the
        attribute, i.e., 'group', is set to the parent group of the attribute.

        If the assigned value is a numerical (scalar or array) or string object,
        it is converted to an object of class NXfield, whose attribute, 
        'nxdata', is set to the assigned value.
        """
        if name.startswith('_') or name.startswith('nx'):
            object.__setattr__(self, name, value)
        elif isinstance(value, NXattr):
            if self.nxfilemode == 'r':
                raise NeXusError("NeXus file opened as readonly")
            self._attrs[name] = value
        else:
            self[name] = value

    def __delattr__(self, name):
        if name in self.entries:
            raise NeXusError(
                "Members can only be deleted using the group dictionary")
        else:
            object.__delattr__(self, name)

    def __getitem__(self, key):
        """
        Returns an entry in the group.
        """
        if is_text(key):
            if '/' in key:
                if key.startswith('/'):
                    return self.nxroot[key[1:]]
                names = [name for name in key.split('/') if name]
                node = self
                for name in names:
                    if name in node:
                        node = node.entries[name]
                    else:
                        raise NeXusError("Invalid path")
                return node
            else:
                return self.entries[key]
        else:
            raise NeXusError("Invalid index")

    def __setitem__(self, key, value):
        """
        Adds or modifies an item in the NeXus group.
        """
        if is_text(key):
            group = self
            if '/' in key:
                names = [name for name in key.split('/') if name]
                key = names.pop()
                for name in names:
                    if name in group:
                        group = group[name]
                    else:
                        print(key, value)
                        raise NeXusError("Invalid path")
            if group.nxfilemode == 'r':
                raise NeXusError("NeXus group marked as readonly")
            elif isinstance(value, NXroot):
                raise NeXusError(
                    "Cannot assign an NXroot group to another group")
            elif key in group:
                if isinstance(value, NXgroup):
                    raise NeXusError(
                        "Cannot assign an NXgroup to an existing group entry")
                elif isinstance(value, NXlink):
                    raise NeXusError(
                        "Cannot assign an NXlink to an existing group entry")
                elif isinstance(group.entries[key], NXlink):
                    raise NeXusError("Cannot assign values to an NXlink")
                group.entries[key].nxdata = value
                if isinstance(value, NXfield):
                    group.entries[key]._setattrs(value.attrs)
            elif isinstance(value, NXobject):
                if value._group:
                    value = deepcopy(value)
                value._group = group
                value._name = key
                if isinstance(value, NXlink):
                    value.initialize_link()
                group.entries[key] = value
            else:
                group.entries[key] = NXfield(value=value, name=key, group=group)
            if isinstance(group.entries[key], NXfield):
                field = group.entries[key]
                if not field._value is None:
                    if isinstance(field._value, np.ma.MaskedArray):
                        mask_name = field._create_mask()
                        group[mask_name] = field._value.mask
                elif field._memfile is not None:
                    if 'mask' in field._memfile:
                        mask_name = field._create_mask()
                        group[mask_name]._create_memfile()
                        field._memfile.copy('mask', group[mask_name]._memfile, 
                                            'data')
                        del field._memfile['mask']
            elif (isinstance(group.entries[key], NXentry) and 
                  not isinstance(group, NXroot)):
                  group.entries[key].nxclass = NXsubentry
            group.entries[key].update()
        else:
            raise NeXusError("Invalid key")

    def __delitem__(self, key):
        if self.nxfilemode == 'r':
            raise NeXusError("NeXus file opened as readonly")
        if is_text(key): #i.e., deleting a NeXus object
            group = self
            if '/' in key:
                names = [name for name in key.split('/') if name]
                key = names.pop()
                for name in names:
                    if name in group:
                        group = group[name]
                    else:
                        raise NeXusError("Invalid path")
            if key not in group:
                raise NeXusError("'"+key+"' not in "+group.nxpath)
            if group.nxfilemode == 'rw':
                with group.nxfile as f:
                    if 'mask' in group.entries[key].attrs:
                        del f[group.entries[key].mask.nxpath]
                    del f[group.entries[key].nxpath]
            if 'mask' in group.entries[key].attrs:
                del group.entries[group.entries[key].mask.nxname]
            del group.entries[key]
            group.set_changed()

    def __contains__(self, key):
        """
        Implements 'k in d' test using the group's entries.
        """
        if isinstance(self, NXroot) and key == '/':
            return True
        elif isinstance(key, NXobject):
            return id(key) in [id(x) for x in self.entries.values()]
        else:
            try:
                return isinstance(self[key], NXobject)		
            except Exception:		
                return False

    def __eq__(self, other):
        """
        Compares the entries dictionaries
        """
        if not isinstance(other, NXgroup): 
            return False
        elif id(self) == id(other):
            return True
        else:
            return self.entries == other.entries

    def __iter__(self):
        """
        Implements key iteration
        """
        return self.entries.__iter__()

    def __len__(self):
        """
        Returns the number of entries in the group
        """
        return len(self.entries)

    def __nonzero__(self):
        """
        Return confirmation that the group exists.
        """
        return True

    def __deepcopy__(self, memo):
        obj = self
        dpcpy = obj.__class__()
        dpcpy._name = self._name
        memo[id(self)] = dpcpy
        dpcpy._changed = True
        for k,v in obj.items():
            if isinstance(v, NXlink):
                v = v.nxlink
            dpcpy.entries[k] = deepcopy(v, memo)
            dpcpy.entries[k]._group = dpcpy
        for k, v in obj.attrs.items():
            dpcpy.attrs[k] = copy(v)
        if 'target' in dpcpy.attrs:
            del dpcpy.attrs['target']
        dpcpy._group = None
        return dpcpy

    def walk(self):
        yield self
        for node in self.values():
            for child in node.walk():
                yield child

    def update(self):
        """
        Updates the NXgroup, including its children, to the NeXus file.
        """
        if self.nxfilemode == 'rw':
            with self.nxfile as f:
                f.update(self)
        elif self.nxfilemode is None:
            for node in self.walk():
                if isinstance(node, NXfield) and node._uncopied_data:
                    node._value = node._get_uncopied_data()
        self.set_changed()

    def get(self, name, default=None):
        """
        Retrieves the group entry, or return default if it doesn't exist
        """
        try:
            return self.entries[name]
        except KeyError:
            return default
            
    def keys(self):
        """
        Returns the names of NeXus objects in the group.
        """
        return self.entries.keys()

    def iterkeys(self):
        """ 
        Get an iterator over group object names
        """
        return iter(self.entries)

    def values(self):
        """
        Returns the values of NeXus objects in the group.
        """
        return self.entries.values()

    def itervalues(self):
        """
        Get an iterator over group objects
        """
        for key in self.entries:
            yield self.entries.get(key)

    def items(self):
        """
        Returns a list of the NeXus objects in the group as (key,value) pairs.
        """
        return self.entries.items()

    def iteritems(self):
        """
        Get an iterator over (name, object) pairs
        """
        for key in self.entries:
            yield (key, self.entries.get(key))

    def has_key(self, name):
        """
        Returns true if a NeXus object with the specified name is in the group.
        """
        return name in self.entries   

    def copy(self):
        """
        Returns a copy of the group's entries
        """
        return deepcopy(self)

    def clear(self):
        raise NeXusError("This method is not implemented for NXgroups")

    def pop(self, *args, **kwargs):
        raise NeXusError("This method is not implemented for NXgroups")

    def popitem(self, *args, **kwargs):
        raise NeXusError("This method is not implemented for NXgroups")

    def fromkeys(self, *args, **kwargs):
        raise NeXusError("This method is not implemented for NXgroups")

    def setdefault(self, *args, **kwargs):
        raise NeXusError("This method is not implemented for NXgroups")

    def component(self, nxclass):
        """
        Finds all child objects that have a particular class.
        """
        return [self.entries[i] for i in sorted(self.entries, key=natural_sort)
                if self.entries[i].nxclass==nxclass]

    def insert(self, value, name='unknown'):
        """
        Adds an attribute to the group.

        If it is not a valid NeXus object, the attribute is converted to an 
        NXfield. If the object is an internal link within an externally linked
        file, the linked object in the external file is copied.
        """
        if isinstance(value, NXobject):
            if name == 'unknown': 
                name = value.nxname
            if name in self.entries:
                raise NeXusError("'%s' already exists in group" % name)
            self[name] = value
            self.update()
        else:
            if name in self.entries:
                raise NeXusError("'%s' already exists in group" % name)
            self[name] = NXfield(value=value, name=name, group=self)

    def makelink(self, target, name=None, abspath=False):
        """
        Creates a linked NXobject within the group.

        The argument is the parent object. All attributes are inherited from the 
        parent object including the name.
        
        The root of the target and child's group must be the same.
        """
        if isinstance(target, NXlink):
            raise NeXusError("Cannot link to an NXlink object")
        elif not isinstance(target, NXobject):
            raise NeXusError("Link target must be an NXobject")
        elif not isinstance(self.nxroot, NXroot):
            raise NeXusError(
                "The group must have a root object of class NXroot")
        elif target.is_external():
            raise NeXusError(
                "Cannot link to an object in an externally linked group")
        if name is None:
            name = target.nxname
        if name in self:
            raise NeXusError("Object with the same name already exists in '%s'" 
                             % self.nxpath)        
        if self.nxroot == target.nxroot:
            self[name] = NXlink(target=target)
        else:
            self[name] = NXlink(target=target.nxpath, file=target.nxfilename,
                                abspath=abspath)
 
    def sum(self, axis=None, averaged=False):
        """
        Returns the sum of the NXdata group using the Numpy sum method
        on the NXdata signal. The sum is over a single axis or a tuple of axes
        using the Numpy sum method.

        The result contains a copy of all the metadata contained in
        the NXdata group.
        """
        if self.nxsignal is None:
            raise NeXusError("No signal to sum")
        if not hasattr(self,"nxclass"):
            raise NeXusError("Summing not allowed for groups of unknown class")
        if axis is None:
            if averaged:
                return self.nxsignal.sum() / self.nxsignal.size
            else:
                return self.nxsignal.sum()
        else:
            if isinstance(axis, numbers.Integral):
                axis = [axis]
            axis = tuple(axis)
            signal = NXfield(self.nxsignal.sum(axis), name=self.nxsignal.nxname,
                             attrs=self.nxsignal.safe_attrs)
            axes = self.nxaxes
            averages = []
            for ax in axis:
                summedaxis = deepcopy(axes[ax])
                summedaxis.attrs["minimum"] = summedaxis.nxdata[0]
                summedaxis.attrs["maximum"] = summedaxis.nxdata[-1]
                summedaxis.attrs["summed_bins"] = summedaxis.size
                averages.append(NXfield(
                    0.5*(summedaxis.nxdata[0]+summedaxis.nxdata[-1]), 
                    name=summedaxis.nxname,attrs=summedaxis.attrs))
            axes = [axes[i] for i in range(len(axes)) if i not in axis]
            result = NXdata(signal, axes)
            summed_bins = 1
            for average in averages:
                result.insert(average)
                summed_bins *= average.attrs["summed_bins"]
            if averaged:
                result.nxsignal = result.nxsignal / summed_bins
                result.attrs["averaged_bins"] = summed_bins
            else:
                result.attrs["summed_bins"] = summed_bins
            if self.nxerrors:
                errors = np.sqrt((self.nxerrors.nxdata**2).sum(axis))
                if averaged:
                    result.nxerrors = NXfield(errors) / summed_bins
                else:
                    result.nxerrors = NXfield(errors)
            if self.nxtitle:
                result.title = self.nxtitle
            return result

    def average(self, axis=None):
        """
        Returns the sum of the NXdata group using the Numpy sum method
        on the NXdata signal. The result is then divided by the number of 
        summed bins to produce an average.

        The result contains a copy of all the metadata contained in
        the NXdata group.
        """
        return self.sum(axis, averaged=True)

    def moment(self, order=1, center=None):
        """
        Returns an NXfield containing the central moments of the NXdata group
        assuming the signal is one-dimensional.
        """
        signal, axes = self.nxsignal, self.nxaxes
        if signal is None:
            raise NeXusError("No signal to calculate")
        elif len(signal.shape) > 1:
            raise NeXusError(
                "Operation only possible on one-dimensional signals")
        if not hasattr(self, "nxclass"):
            raise NeXusError(
                "Operation not allowed for groups of unknown class")
        y = signal / signal.sum()
        x = centers(y, axes)[0]
        if center:
            c = center
        else:
            c = (y * x).sum()
        if order == 1:
            return c
        else:
            return (y * (x - c)**order).sum()

    def mean(self):
        """
        Returns an NXfield containing the mean of the NXdata group
        assuming the signal is one-dimensional.
        """
        return self.moment(1)

    def var(self):
        """
        Returns an NXfield containing the variance of the NXdata group
        assuming the signal is one-dimensional.
        """
        return self.moment(2)

    def std(self):
        """
        Returns an NXfield containing the standard deviation of the NXdata group
        assuming the signal is one-dimensional.
        """
        return np.sqrt(self.moment(2))

    def is_plottable(self):
        plottable = False
        for entry in self:
            if self[entry].is_plottable():
                plottable = True
        return plottable        

    @property
    def plottable_data(self):
        """
        Returns the first NXdata group within the group's tree.
        """
        return None

    def plot(self, **kwargs):
        """
        Plot data contained within the group.
        """
        plotdata = self.plottable_data
        if plotdata:
            plotdata.plot(**kwargs)
        else:
            raise NeXusError("There is no plottable data")

    def oplot(self, **kwargs):
        """
        Plots the data contained within the group over the current figure.
        """
        plotdata = self.plottable_data
        if plotdata:
            plotdata.oplot(**kwargs)
        else:
            raise NeXusError("There is no plottable data")

    def logplot(self, **kwargs):
        """
        Plots the data intensity contained within the group on a log scale.
        """
        plotdata = self.plottable_data
        if plotdata:
            plotdata.logplot(**kwargs)
        else:
            raise NeXusError("There is no plottable data")

    def implot(self, **kwargs):
        """
        Plots the data intensity as an RGB(A) image.
        """
        plotdata = self.plottable_data
        if plotdata:
            plotdata.implot(**kwargs)
        else:
            raise NeXusError("There is no plottable data")

    def signals(self):
        """
        Returns a dictionary of NXfield's containing signal data.

        The key is the value of the signal attribute.
        """
        signals = {}
        for obj in self.values():
            if 'signal' in obj.attrs:
                signals[obj.attrs['signal']] = obj
        return signals

    def _str_name(self, indent=0):
        return " " * indent + self.nxname + ':' + self.nxclass

    def _str_tree(self, indent=0, attrs=False, recursive=False):
        """
        Prints the current object and children (if any).
        """
        result = [self._str_name(indent=indent)]
        if self.attrs and (attrs or indent==0):
            result.append(self._str_attrs(indent=indent+2))
        entries = self.entries
        if entries:
            names = sorted(entries, key=natural_sort)
            if recursive:
                if recursive is True or recursive >= indent:
                    for k in names:
                        result.append(entries[k]._str_tree(indent=indent+2,
                                                           attrs=attrs, 
                                                           recursive=recursive))
            else:
                for k in names:
                    result.append(entries[k]._str_name(indent=indent+2))
        return "\n".join(result)

    @property
    def nxtitle(self):
        """
        Returns the title as a string.

        If there is no title field in the group or its parent group, the group's
        path is returned.
        """
        if 'title' in self:
            return text(self.title)
        elif self.nxgroup and 'title' in self.nxgroup:
            return text(self.nxgroup.title)
        else:
            root = self.nxroot
            if root.nxname != '' and root.nxname != 'root':
                return (root.nxname + '/' + self.nxpath.lstrip('/')).rstrip('/')
            else:
                fname = self.nxfilename
                if fname is not None:
                    return fname + ':' + self.nxpath
                else:
                    return self.nxpath

    @property
    def entries(self):
        return self._entries

    nxsignal = None
    nxaxes = None
    nxerrors = None


class NXlink(NXobject):

    """
    Class for NeXus linked objects.

    The real object will be accessible by following the link attribute.
    """

    _class = "NXlink"

    def __init__(self, target=None, file=None, name=None, group=None, 
                 abspath=False):
        self._class = "NXlink"
        self._name = name
        self._group = group
        self._abspath = abspath
        if file is not None:
            self._filename = file
            self._mode = 'r'
        else:
            self._filename = self._mode = None
        self._attrs = AttrDict(self)
        self._entries = {}
        if isinstance(target, NXobject):
            if isinstance(target, NXlink):
                raise NeXusError("Cannot link to another NXlink object")
            if name is None:
                self._name = target.nxname
            self._target = target.nxpath
            if isinstance(target, NXfield):
                self._setclass(NXlinkfield)
            elif isinstance(target, NXgroup):
                self._setclass(_getclass(target.nxclass, link=True))
        else:
            if name is None and is_text(target):
                self._name = target.rsplit('/', 1)[1]
            self._target = text(target)
        self._link = None

    def __repr__(self):
        if self._filename:
            return "NXlink(target='%s', file='%s')" % (self._target, 
                                                       self._filename)
        else:
            return "NXlink('%s')" % (self._target)

    def __getattr__(self, name):
        if self.is_external():
            if self.exists():
                with self.nxfile as f:
                    item = f.readpath(self.nxfilepath)
                return getattr(item, name)
            else:
                raise NeXusError("Cannot read the external link to '%s'" % self._filename)
        else:
            if self.nxlink:
                return getattr(self.nxlink, name)
            else:
                raise NeXusError("Cannot resolve the link to '%s'" % self._target)

    def __setattr__(self, name, value):
        if name.startswith('_')  or name.startswith('nx'):
            object.__setattr__(self, name, value)
        elif self.is_external():
            raise NeXusError("Cannot modify an externally linked file")
        else:
            self.nxlink.__setattr__(name, value)            

    def __deepcopy__(self, memo={}):
        obj = self
        dpcpy = obj.__class__()
        memo[id(self)] = dpcpy
        dpcpy._name = copy(self.nxname)
        dpcpy._target = copy(obj._target)
        if obj._filename:
            dpcpy._filename = copy(obj.nxfilename)
        else:
            dpcpy._filename = None
        dpcpy._abspath = copy(obj._abspath)
        dpcpy._link = None
        dpcpy._group = None
        return dpcpy

    def _str_name(self, indent=0):
        if self._filename:
            return (" " * indent + self.nxname + ' -> ' + text(self._filename) +
                    "['" + text(self._target) + "']")
        else:
            return " " * indent + self.nxname + ' -> ' + text(self._target)

    def _str_tree(self, indent=0, attrs=False, recursive=False):
        return self._str_name(indent=indent)

    def update(self):
        root = self.nxroot
        filename, mode = root.nxfilename, root.nxfilemode
        if (filename is not None and os.path.exists(filename) and mode == 'rw'):
            with root.nxfile as f:
                f.update(self)
        self.set_changed()

    @property
    def nxlink(self):
        if self._link is None:
            self.initialize_link()
        return self._link

    def initialize_link(self):
        """Determine the link class from the target."""
        if self._link is None:
            if self._filename is not None and os.path.exists(self.nxfilename):
                with self.nxfile as f:
                    item = f.readpath(self.nxfilepath)
                self._link = self
            elif self._target in self.nxroot:
                item = self.nxroot[self._target]
                self._link = item
            else:
                self._link = None
                return None
            if isinstance(item, NXfield):
                self._setclass(NXlinkfield)
            elif isinstance(item, NXgroup):
                self._setclass(_getclass(item.nxclass, link=True))
            self.copy(item)
        return self._link

    @property
    def nxfilemode(self):
        try:
            if self._mode is None:
                if self.is_external():
                    self._mode = 'r'
                else:
                    self._mode = self.nxlink.nxfilemode
            return self._mode
        except Exception:
            return 'r'

    @property
    def attrs(self):
        try:
            if not self.is_external():
                return self.nxlink._attrs
            else:
                return self._attrs
        except Exception as error:
            self._attrs = AttrDict(self)
        return self._attrs

    @property
    def abspath(self):
        return self._abspath

    def is_external(self):
        if self._external is None:
            if self._filename is not None:
                self._external = True
            else:
                self._external = super(NXlink, self).is_external()
        return self._external


class NXlinkfield(NXlink, NXfield):

    """
    Class for a NeXus linked field.

    The real field will be accessible by following the link attribute.
    """
    def __init__(self, target=None, file=None, name=None, abspath=False, 
                 **kwargs):
        NXlink.__init__(self, target=target, file=file, name=name, 
                        abspath=abspath)
        if self._filename is not None:
            NXfield.__init__(self, name=name, **kwargs)
        self._class = "NXfield"

    def __getitem__(self, key):
        if self.is_external():
            return super(NXlinkfield, self).__getitem__(key)
        else:
            return self.nxlink.__getitem__(key)

    def __setitem__(self, key, value):
        if self.is_external():
            raise NeXusError("Cannot modify an externally linked file")
        else:
            self.nxlink.__setitem__(key, value)

    def copy(self, field):
        self._value = field._value
        self._shape = field._shape
        self._dtype = field._dtype
        self._attrs = field._attrs
        self._h5opts = field._h5opts
        self._memfile = field._memfile
        self._uncopied_data = field._uncopied_data
        self._attrs = field._attrs

    def plot(self, **kwargs):
        if self.is_external():
            super(NXlinkfield, self).plot(**kwargs)
        else:
            self.nxlink.plot(**kwargs)            


class NXlinkgroup(NXlink, NXgroup):

    """
    Class for a NeXus linked group.

    The real group will be accessible by following the link attribute.
    """
    def __init__(self, target=None, file=None, name=None, abspath=False, **kwargs):
        NXlink.__init__(self, target=target, file=file, name=name, 
                        abspath=abspath)
        if 'nxclass' in kwargs:
            NXgroup.__init__(self, **kwargs)
            self._setclass(_getclass(kwargs['nxclass'], link=True))
        else:
            self._class = 'NXlink'

    def __getitem__(self, key):
        if self.is_external():
            return self._entries[key]
        else:
            return self.nxlink.__getitem__(key)

    def __setitem__(self, key, value):
        if self.is_external():
            raise NeXusError("Cannot modify an externally linked file")
        else:
            self.nxlink.__setitem__(key, value)

    def _str_name(self, indent=0):
        if self._filename:
            return (" " * indent + self.nxname + ':' + self.nxclass + 
                    ' -> ' + text(self._filename) + 
                    "['" + text(self._target) + "']")
        else:
            return (" " * indent + self.nxname + ':' + self.nxclass + 
                    ' -> ' + text(self._target))

    def _str_tree(self, indent=0, attrs=False, recursive=False):
        try:
            return NXgroup._str_tree(self, indent=indent, attrs=attrs, 
                                     recursive=recursive)
        except Exception:
            return NXlink(self)._str_tree(self, indent=indent)
        
    def copy(self, group):
        self._entries = group._entries
        self._attrs = group._attrs

    @property
    def entries(self):
        return self.nxlink._entries

    def plot(self, **kwargs):
        if self.is_external():
            super(NXlinkgroup, self).plot(**kwargs)
        else:
            self.nxlink.plot(**kwargs)        


class NXroot(NXgroup):

    """
    NXroot group. This is a subclass of the NXgroup class.

    This group has additional methods to lock or unlock the tree.

    See the NXgroup documentation for more details.
    """

    def __init__(self, *args, **kwargs):
        self._class = "NXroot"
        self._backup = None
        self._mtime = None
        self._file_modified = False
        NXgroup.__init__(self, *args, **kwargs)

    def reload(self):
        if self.nxfilemode:
            with self.nxfile as f:
                f.reload()
            self.set_changed()
        else:
            raise NeXusError("'%s' has no associated file to reload" % self.nxname)

    def is_modified(self):
        try:
            _mtime = self.nxfile.mtime
            if self._mtime and _mtime > self._mtime:
                self._file_modified = True
                return True
            else:
                self._file_modified = False
                return False
        except (AttributeError, TypeError, FileNotFoundError):
            self._file_modified = False
            return False

    def lock(self):
        """Make the tree readonly"""
        if self._filename:
            if self.file_exists():
                self._mode = self._file.mode = 'r'
                self.set_changed()
            else:
                raise NeXusError("'%s' does not exist" % 
                                 os.path.abspath(self.nxfilename))

    def unlock(self):
        """Make the tree modifiable"""
        if self._filename:
            if self.file_exists():
                if self.is_modified():
                    raise NeXusError("File modified. Reload before unlocking")
                self._mode = self._file.mode = 'rw'
            else:
                self._mode = None
                self._file = None
                raise NeXusError("'%s' does not exist" % 
                                 os.path.abspath(self.nxfilename))
            self.set_changed()

    def backup(self, filename=None, dir=None):
        """Backup the NeXus file.
        
        If no backup file is given, the backup is saved to the current
        directory with a randomized name.
        """ 
        if self.nxfilemode is None:
            raise NeXusError("Only data saved to a NeXus file can be backed up")
        if filename is None:
            if dir is None:
                dir = os.getcwd()
            import tempfile
            prefix, suffix = os.path.splitext(os.path.basename(self.nxfilename))
            prefix = prefix + '_backup_'
            backup = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=dir)[1]
        else:
            if dir is not None:
                filename = os.path.join(dir, filename)
            if os.path.exists(filename):
                raise NeXusError("'%s' already exists" 
                                 % os.path.abspath(filename))
            else:
                backup = os.path.abspath(filename)
        import shutil
        shutil.copy2(self.nxfilename, backup)
        self._backup = backup

    def restore(self, filename=None, overwrite=False):
        """Restore the backup.
        
        If no file name is given, the backup replaces the current NeXus file
        provided 'overwrite' has been set to True."""
        if self._backup is None:
            raise NeXusError("No backup exists")
        if filename is None:
            filename = self.nxfilename
        if os.path.exists(filename) and not overwrite:
            raise NeXusError("To overwrite '%s', set 'overwite' to True"
                             % os.path.abspath(filename))
        import shutil
        shutil.copy2(self._backup, filename)
        self.nxfile = filename

    def close(self):
        """Close the underlying HDF5 file."""
        if self.nxfile:
            self.nxfile.close()

    @property
    def plottable_data(self):
        """
        Returns the first NXdata group within the group's tree.
        """
        if 'default' in self.attrs and self.attrs['default'] in self:
            group = self[self.attrs['default']]
            if isinstance(group, NXdata):
                return group
            elif isinstance(group, NXentry):
                plottable_data = group.plottable_data
                if isinstance(plottable_data, NXdata):
                    return plottable_data
        if self.NXdata:
            return self.NXdata[0]
        elif self.NXmonitor:
            return self.NXmonitor[0]
        elif self.NXlog:
            return self.NXlog[0]
        elif self.NXentry:
            for entry in self.NXentry:
                data = entry.plottable_data
                if data is not None:
                    return data
        return None

    @property
    def nxfile(self):
        if self._file:
            return self._file
        elif self._filename:
            self._file = NXFile(self._filename, self._mode)
            return self._file
        else:
            return None

    @nxfile.setter
    def nxfile(self, filename):
        if os.path.exists(filename):
            self._filename = os.path.abspath(filename)
            with NXFile(self._filename, 'r') as f:
                root = f.readfile()
            self._entries = root._entries
            for entry in self._entries:
                self._entries[entry]._group = self
            self._attrs._setattrs(root.attrs)
            self._file = NXFile(self._filename, self._mode)
            self.set_changed()
        else:
            raise NeXusError("'%s' does not exist" % os.path.abspath(filename))

    @property
    def nxbackup(self):
        """Returns name of backup file if it exists"""
        return self._backup

    @property
    def mtime(self):
        """Return modification time of last change to root group."""
        return self._mtime


class NXentry(NXgroup):

    """
    NXentry group. This is a subclass of the NXgroup class.

    Each NXdata and NXmonitor object of the same name will be added
    together, raising an NeXusError if any of the groups do not exist
    in both NXentry groups or if any of the NXdata additions fail.
    The resulting NXentry group contains a copy of all the other metadata
    contained in the first group. Note that other extensible data, such
    as the run duration, are not currently added together.

    See the NXgroup documentation for more details.
    """

    def __init__(self, *args, **kwargs):
        self._class = "NXentry"
        NXgroup.__init__(self, *args, **kwargs)

    def __add__(self, other):
        """
        Adds two NXentry objects
        """
        result = NXentry(entries=self.entries, attrs=self.attrs)
        try:
            names = [group.nxname for group in self.component("NXdata")]
            for name in names:
                if isinstance(other[name], NXdata):
                    result[name] = self[name] + other[name]
                else:
                    raise KeyError
            names = [group.nxname for group in self.component("NXmonitor")]
            for name in names:
                if isinstance(other[name], NXmonitor):
                    result[name] = self[name] + other[name]
                else:
                    raise KeyError
            return result
        except KeyError:
            raise NeXusError("Inconsistency between two NXentry groups")

    def __sub__(self, other):
        """
        Subtracts two NXentry objects
        """
        result = NXentry(entries=self.entries, attrs=self.attrs)
        try:
            names = [group.nxname for group in self.component("NXdata")]
            for name in names:
                if isinstance(other[name], NXdata):
                    result[name] = self[name] - other[name]
                else:
                    raise KeyError
            names = [group.nxname for group in self.component("NXmonitor")]
            for name in names:
                if isinstance(other[name], NXmonitor):
                    result[name] = self[name] - other[name]
                else:
                    raise KeyError
            return result
        except KeyError:
            raise NeXusError("Inconsistency between two NXentry groups")

    @property
    def plottable_data(self):
        """
        Returns the first NXdata group within the group's tree.
        """
        if 'default' in self.attrs and self.attrs['default'] in self:
            plottable_data = self[self.attrs['default']]
            if isinstance(plottable_data, NXdata):
                return plottable_data
        if self.NXdata:
            return self.NXdata[0]
        elif self.NXmonitor:
            return self.NXmonitor[0]
        elif self.NXlog:
            return self.NXlog[0]
        else:
            return None


class NXsubentry(NXentry):

    """
    NXsubentry group. This is a subclass of the NXsubentry class.

    See the NXgroup documentation for more details.
    """

    def __init__(self, *args, **kwargs):
        self._class = "NXsubentry"
        NXgroup.__init__(self, *args, **kwargs)


class NXdata(NXgroup):

    """
    NXdata group. This is a subclass of the NXgroup class.

    The constructor assumes that the first argument contains the signal and
    the second contains either the axis, for one-dimensional data, or a list
    of axes, for multidimensional data. These arguments can either be NXfield
    objects or Numpy arrays, which are converted to NXfield objects with default
    names. Alternatively, the signal and axes NXfields can be defined using the
    'nxsignal' and 'nxaxes' properties. See the examples below.
    
    Various arithmetic operations (addition, subtraction, multiplication,
    and division) have been defined for combining NXdata groups with other
    NXdata groups, Numpy arrays, or constants, raising a NeXusError if the
    shapes don't match. Data errors are propagated in quadrature if
    they are defined, i.e., if the 'nexerrors' attribute is not None,

    **Python Attributes**

    nxsignal : property
        The NXfield containing the attribute 'signal' with value 1
    nxaxes : property
        A list of NXfields containing the signal axes
    nxerrors : property
        The NXfield containing the errors

    **Examples**

    There are three methods of creating valid NXdata groups with the
    signal and axes NXfields defined according to the NeXus standard.
    
    1) Create the NXdata group with Numpy arrays that will be assigned
       default names.
       
       >>> x = np.linspace(0, 2*np.pi, 101)
       >>> line = NXdata(sin(x), x)
       data:NXdata
         signal = float64(101)
           @axes = x
           @signal = 1
         axis1 = float64(101)
      
    2) Create the NXdata group with NXfields that have their internal
       names already assigned.

       >>> x = NXfield(linspace(0,2*pi,101), name='x')
       >>> y = NXfield(linspace(0,2*pi,101), name='y')    
       >>> X, Y = np.meshgrid(x, y)
       >>> z = NXfield(sin(X) * sin(Y), name='z')
       >>> entry = NXentry()
       >>> entry.grid = NXdata(z, (x, y))
       >>> grid.tree()
       entry:NXentry
         grid:NXdata
           x = float64(101)
           y = float64(101)
           z = float64(101x101)
             @axes = x:y
             @signal = 1

    3) Create the NXdata group with keyword arguments defining the names 
       and set the signal and axes using the nxsignal and nxaxes properties.

       >>> x = linspace(0,2*pi,101)
       >>> y = linspace(0,2*pi,101)  
       >>> X, Y = np.meshgrid(x, y)
       >>> z = sin(X) * sin(Y)
       >>> entry = NXentry()
       >>> entry.grid = NXdata(z=sin(X)*sin(Y), x=x, y=y)
       >>> entry.grid.nxsignal = entry.grid.z
       >>> entry.grid.nxaxes = [entry.grid.x,entry.grid.y]
       >>> grid.tree()
       entry:NXentry
         grid:NXdata
           x = float64(101)
           y = float64(101)
           z = float64(101x101)
             @axes = x:y
             @signal = 1
    """

    def __init__(self, signal=None, axes=None, errors=None, *args, **kwargs):
        self._class = 'NXdata'
        NXgroup.__init__(self, *args, **kwargs)
        attrs = {}
        if axes is not None:
            if not is_iterable(axes):
                axes = [axes]
            axis_names = {}
            i = 0
            for axis in axes:
                i += 1
                if isinstance(axis, NXfield) or isinstance(axis, NXlink):
                    if axis.nxname == 'unknown' or axis.nxname in self: 
                        axis_name = 'axis%s' % i
                    else:
                        axis_name = axis.nxname
                else:
                    axis_name = 'axis%s' % i
                self[axis_name] = axis
                axis_names[i] = axis_name
            attrs['axes'] = list(axis_names.values())
        if signal is not None:
            if isinstance(signal, NXfield) or isinstance(signal, NXlink):
                if signal.nxname == 'unknown' or signal.nxname in self:
                    signal_name = 'signal'
                else:
                    signal_name = signal.nxname
            else:
                signal_name = 'signal'
            self[signal_name] = signal
            attrs['signal'] = signal_name
            if errors is not None:
                if isinstance(errors, NXfield) or isinstance(errors, NXlink):
                    if errors.nxname == 'unknown' or errors.nxname in self:
                        errors_name = signal_name+'_errors'
                    else:
                        errors_name = errors.nxname
                else:
                    errors_name = signal_name+'_errors'
                self[errors_name] = errors
                self[signal_name].attrs['uncertainties'] = errors_name
        self.attrs._setattrs(attrs)

    def __setattr__(self, name, value):
        """
        Sets an attribute as an object or regular Python attribute.

        This calls the NXgroup __setattr__ function unless the name is 'mask'
        which is used to set signal masks.
        """
        if name == 'mask':
            object.__setattr__(self, name, value)
        else:
            super(NXdata, self).__setattr__(name, value)

    def __getitem__(self, key):
        """
        Returns an entry in the group if the key is a string.
        
        or
        
        Returns a slice from the NXgroup nxsignal attribute (if it exists) as
        a new NXdata group, if the index is a slice object.

        In most cases, the slice values are applied to the NXfield nxdata array
        and returned within an NXfield object with the same metadata. However,
        if the array is one-dimensional and the index start and stop values
        are real, the nxdata array is returned with values between the limits
        set by those axis values.

        This is to allow axis arrays to be limited by their actual value. This
        real-space slicing should only be used on monotonically increasing (or
        decreasing) one-dimensional arrays.
        """
        if is_text(key): #i.e., requesting a dictionary value
            return NXgroup.__getitem__(self, key)
        elif self.nxsignal is not None:
            idx, axes = self.slab(key)
            removed_axes = []
            for axis in axes:
                if axis.shape == () or axis.shape == (0,) or axis.shape == (1,):
                    removed_axes.append(axis)
            axes = [ax for ax in axes if ax not in [rax for rax in removed_axes 
                                                    if rax is ax]]            
            signal = self.nxsignal[idx]
            if self.nxerrors: 
                errors = self.nxerrors[idx]
            else:
                errors = None
            if 'axes' in signal.attrs:
                del signal.attrs['axes']
            result = NXdata(signal, axes, errors, *removed_axes)
            if errors is not None:
                result.nxerrors = errors
            if self.nxsignal.mask is not None:
                if isinstance(self.nxsignal.mask, NXfield):
                    result[self.nxsignal.mask.nxname] = signal.mask 
            if self.nxtitle:
                result.title = self.nxtitle
            return result
        else:
            raise NeXusError("No signal specified")

    def __setitem__(self, idx, value):
        if is_text(idx):
            NXgroup.__setitem__(self, idx, value)
        elif self.nxsignal is not None:
            if isinstance(idx, numbers.Integral) or isinstance(idx, slice):
                axis = self.nxaxes[0]
                if self.nxsignal.shape[0] == axis.shape[0]:
                    axis = axis.boundaries()
                idx = convert_index(idx, axis)
                self.nxsignal[idx] = value
            else:
                slices = []
                axes = self.nxaxes
                for i,ind in enumerate(idx):
                    if self.nxsignal.shape[i] == axes[i].shape[0]:
                        axis = axes[i].boundaries()
                    else:
                        axis = axes[i]
                    ind = convert_index(ind, axis)
                    if isinstance(ind, slice) and ind.stop is not None:
                        ind = slice(ind.start, ind.stop-1, ind.step)
                    slices.append(ind)
                self.nxsignal[tuple(slices)] = value
        else:
            raise NeXusError("Invalid index")

    def __delitem__(self, key):
        super(NXdata, self).__delitem__(key)
        if 'signal' in self.attrs and self.attrs['signal'] == key:
            del self.attrs['signal']
        elif 'axes' in self.attrs:
            self.attrs['axes'] = [ax if ax != key else '.'
                                  for ax in _readaxes(self.attrs['axes'])]

    def __add__(self, other):
        """
        Adds the NXdata group to another NXdata group or to a number. Only the 
        signal data is affected.

        The result contains a copy of all the metadata contained in
        the first NXdata group. The module checks that the dimensions are
        compatible, but does not check that the NXfield names or values are
        identical. This is so that spelling variations or rounding errors
        do not make the operation fail. However, it is up to the user to
        ensure that the results make sense.
        """
        result = NXdata(entries=self.entries, attrs=self.attrs)
        if isinstance(other, NXdata):
            if self.nxsignal and self.nxsignal.shape == other.nxsignal.shape:
                result[self.nxsignal.nxname] = self.nxsignal + other.nxsignal
                if self.nxerrors:
                    if other.nxerrors:
                        result.nxerrors = np.sqrt(self.nxerrors**2 + 
                                                  other.nxerrors**2)
                    else:
                        result.nxerrors = self.nxerrors
                return result
        elif isinstance(other, NXgroup):
            raise NeXusError("Cannot add two arbitrary groups")
        else:
            result[self.nxsignal.nxname] = self.nxsignal + other
            return result

    def __sub__(self, other):
        """
        Subtracts a NXdata group or a number from the NXdata group. Only the 
        signal data is affected.

        The result contains a copy of all the metadata contained in
        the first NXdata group. The module checks that the dimensions are
        compatible, but does not check that the NXfield names or values are
        identical. This is so that spelling variations or rounding errors
        do not make the operation fail. However, it is up to the user to
        ensure that the results make sense.
        """
        result = NXdata(entries=self.entries, attrs=self.attrs)
        if isinstance(other, NXdata):
            if self.nxsignal and self.nxsignal.shape == other.nxsignal.shape:
                result[self.nxsignal.nxname] = self.nxsignal - other.nxsignal
                if self.nxerrors:
                    if other.nxerrors:
                        result.nxerrors = np.sqrt(self.nxerrors**2 + 
                                                  other.nxerrors**2)
                    else:
                        result.nxerrors = self.nxerrors
                return result
        elif isinstance(other, NXgroup):
            raise NeXusError("Cannot subtract two arbitrary groups")
        else:
            result[self.nxsignal.nxname] = self.nxsignal - other
            return result

    def __mul__(self, other):
        """
        Multiplies the NXdata group with a NXdata group or a number. Only the 
        signal data is affected.

        The result contains a copy of all the metadata contained in
        the first NXdata group. The module checks that the dimensions are
        compatible, but does not check that the NXfield names or values are
        identical. This is so that spelling variations or rounding errors
        do not make the operation fail. However, it is up to the user to
        ensure that the results make sense.
        """
        result = NXdata(entries=self.entries, attrs=self.attrs)
        if isinstance(other, NXdata):

            # error here signal not defined in this scope
            #if self.nxsignal and signal.shape == other.nxsignal.shape:
            if self.nxsignal and self.nxsignal.shape == other.nxsignal.shape:
                result[self.nxsignal.nxname] = self.nxsignal * other.nxsignal
                if self.nxerrors:
                    if other.nxerrors:
                        result.nxerrors = np.sqrt(
                                          (self.nxerrors * other.nxsignal)**2 +
                                          (other.nxerrors * self.nxsignal)**2)
                    else:
                        result.nxerrors = self.nxerrors
                return result
        elif isinstance(other, NXgroup):
            raise NeXusError("Cannot multiply two arbitrary groups")
        else:
            result[self.nxsignal.nxname] = self.nxsignal * other
            if self.nxerrors:
                result.nxerrors = self.nxerrors * other
            return result

    def __rmul__(self, other):
        """
        Multiplies the NXdata group with a NXdata group or a number.

        This variant makes __mul__ commutative.
        """
        return self.__mul__(other)

    def __truediv__(self, other):
        """
        Divides the NXdata group by a NXdata group or a number. Only the signal 
        data is affected.

        The result contains a copy of all the metadata contained in
        the first NXdata group. The module checks that the dimensions are
        compatible, but does not check that the NXfield names or values are
        identical. This is so that spelling variations or rounding errors
        do not make the operation fail. However, it is up to the user to
        ensure that the results make sense.
        """
        result = NXdata(entries=self.entries, attrs=self.attrs)
        if isinstance(other, NXdata):
            if self.nxsignal and self.nxsignal.shape == other.nxsignal.shape:
                result[self.nxsignal.nxname] = self.nxsignal / other.nxsignal
                if self.nxerrors:
                    if other.nxerrors:
                        result.nxerrors = (np.sqrt(self.nxerrors**2 +
                            (result[self.nxsignal.nxname] * other.nxerrors)**2)
                                         / other.nxsignal)
                    else:
                        result.nxerrors = self.nxerrors
                return result
        elif isinstance(other, NXgroup):
            raise NeXusError("Cannot divide two arbitrary groups")
        else:
            result[self.nxsignal.nxname] = self.nxsignal / other
            if self.nxerrors: 
                result.nxerrors = self.nxerrors / other
            return result

    __div__ = __truediv__

    def project(self, axes, limits, summed=True):
        """
        Projects the data along a specified 1D axis or 2D axes summing over the
        limits, which are specified as tuples for each dimension.
        
        This assumes that the data is at least two-dimensional.
        """
        if not is_iterable(axes):
            axes = [axes]
        if len(limits) < len(self.nxsignal.shape):
            raise NeXusError("Too few limits specified")
        elif len(axes) > 2:
            raise NeXusError(
                "Projections to more than two dimensions not supported")
        projection_axes =  sorted([x for x in range(len(limits)) 
                                   if x not in axes], reverse=True)
        idx, _ = self.slab([slice(_min, _max) for _min, _max in limits])
        result = self[idx]
        idx, slab_axes = list(idx), list(projection_axes)
        for slab_axis in slab_axes:
            if isinstance(idx[slab_axis], numbers.Integral):
                idx.pop(slab_axis)
                projection_axes.pop(projection_axes.index(slab_axis))
                for i in range(len(projection_axes)):
                    if projection_axes[i] > slab_axis:
                        projection_axes[i] -= 1
        if projection_axes:
            if summed:
                result = result.sum(projection_axes)
            else:
                result = result.average(projection_axes)
        if len(axes) > 1 and axes[0] > axes[1]:
            signal, errors = result.nxsignal, result.nxerrors
            result[signal.nxname].replace(signal.transpose())
            result.nxsignal = result[signal.nxname]
            if errors:
                result[errors.nxname].replace(errors.transpose())
                result.nxerrors = result[errors.nxname]
            result.nxaxes = result.nxaxes[::-1]            
        return result        

    def slab(self, idx):
        if (isinstance(idx, numbers.Real) or isinstance(idx, numbers.Integral)
                or isinstance(idx, slice)):
            idx = [idx]
        signal = self.nxsignal
        axes = self.nxaxes
        slices = []
        for i,ind in enumerate(idx):
            if is_real_slice(ind):
                if signal.shape[i] == axes[i].shape[0]:
                    axis = axes[i].boundaries()
                else:
                    axis = axes[i]
                ind = convert_index(ind, axis)
                if signal.shape[i] < axes[i].shape[0]:
                    axes[i] = axes[i][ind]
                    if isinstance(ind, slice) and ind.stop is not None:
                        ind = slice(ind.start, ind.stop-1, ind.step)
                elif (signal.shape[i] == axes[i].shape[0]):
                    if isinstance(ind, slice) and ind.stop is not None:
                        ind = slice(ind.start, ind.stop-1, ind.step)
                    axes[i] = axes[i][ind]
                slices.append(ind)
            else:
                ind = convert_index(ind, axes[i])
                slices.append(ind)
                if (isinstance(ind, slice) and ind.stop is not None
                    and signal.shape[i] < axes[i].shape[0]):
                    ind = slice(ind.start, ind.stop+1, ind.step)
                axes[i] = axes[i][ind]
        return tuple(slices), axes

    @property
    def plottable_data(self):
        """
        Returns self.
        """
        if self.nxsignal is not None:
            return self
        else:
            return None

    @property
    def plot_shape(self):
        if self.nxsignal is not None:
            return self.nxsignal.plot_shape
        else:
            return None

    @property
    def plot_rank(self):
        if self.nxsignal is not None:
            return self.nxsignal.plot_rank
        else:
            return None

    @property
    def plot_axes(self):
        signal = self.nxsignal
        if signal is not None:
            if len(signal.shape) > len(signal.plot_shape):
                axes = self.nxaxes
                newaxes = []
                for i in range(signal.ndim):
                    if signal.shape[i] > 1: 
                        newaxes.append(axes[i])
                return newaxes
            else:
                return self.nxaxes
        else:
            return None

    def plot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
             vmin=None, vmax=None, **kwargs):
        """
        Plot data contained within the group.

        The format argument is used to set the color and type of the
        markers or lines for one-dimensional plots, using the standard 
        Matplotlib syntax. The default is set to blue circles. All 
        keyword arguments accepted by matplotlib.pyplot.plot can be
        used to customize the plot.
        
        In addition to the matplotlib keyword arguments, the following
        are defined::
        
            log = True     - plot the intensity on a log scale
            logy = True    - plot the y-axis on a log scale
            logx = True    - plot the x-axis on a log scale
            over = True    - plot on the current figure
            image = True   - plot as an RGB(A) image

        Raises NeXusError if the data could not be plotted.
        """

        # Check there is a plottable signal
        signal = self.nxsignal
        if signal is None:
            raise NeXusError("No plotting signal defined")
        elif not signal.exists():
            raise NeXusError("Data for '%s' does not exist" % signal.nxpath)
        elif not signal.is_plottable():
            raise NeXusError("'%s' is not plottable" % signal.nxpath)
        else:
            axes = self.plot_axes
            if axes is not None and not self.nxsignal.valid_axes(axes):
                raise NeXusError("Defined axes not compatible with the signal")

        # Plot with the available plotter
        try:
            from __main__ import plotview
            if plotview is None:
                raise ImportError
        except ImportError:
            from .plot import plotview
            
        plotview.plot(self, fmt, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, 
                      vmin=vmin, vmax=vmax, **kwargs)
    
    def oplot(self, fmt='', **kwargs):
        """
        Plots the data contained within the group over the current figure.
        """
        self.plot(fmt=fmt, over=True, **kwargs)

    def logplot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
                vmin=None, vmax=None, **kwargs):
        """
        Plots the data intensity contained within the group on a log scale.
        """
        self.plot(fmt=fmt, log=True,
                  xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                  vmin=vmin, vmax=vmax, **kwargs)

    def implot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
                vmin=None, vmax=None, **kwargs):
        """
        Plots the data intensity as an image.
        """
        if (self.nxsignal.plot_rank > 2 and 
            (self.nxsignal.shape[-1] == 3 or self.nxsignal.shape[-1] == 4)):
            self.plot(fmt=fmt, image=True,
                      xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                      vmin=vmin, vmax=vmax, **kwargs)
        else:
            raise NeXusError("Invalid shape for RGB(A) image")

    @property
    def nxsignal(self):
        """
        Returns the NXfield containing the signal data.
        """
        if 'signal' in self.attrs and self.attrs['signal'] in self:
            return self[self.attrs['signal']]
        for obj in self.values():
            if 'signal' in obj.attrs and text(obj.attrs['signal']) == '1':
                if isinstance(self[obj.nxname], NXlink):
                    return self[obj.nxname].nxlink
                else:
                    return self[obj.nxname]
        return None
    
    @nxsignal.setter
    def nxsignal(self, signal):
        """
        Setter for the signal attribute.
        
        The argument should be a valid NXfield within the group.
        """
        current_signal = self.nxsignal
        if current_signal is not None and current_signal is not signal:
            if 'signal' in current_signal.attrs:
                del current_signal.attrs['signal']
        self.attrs['signal'] = signal.nxname
        if signal not in self:
            self[signal.nxname] = signal

    @property
    def nxaxes(self):
        """
        Returns a list of NXfields containing the axes.
        """
        def empty_axis(i):
            return NXfield(np.arange(self.nxsignal.shape[i]), name='Axis%s'%i)
        def plot_axis(axis):
            return NXfield(axis.nxvalue, name=axis.nxname, attrs=axis.attrs) 
        try:
            if 'axes' in self.attrs:
                axis_names = _readaxes(self.attrs['axes'])
            elif self.nxsignal is not None and 'axes' in self.nxsignal.attrs:
                axis_names = _readaxes(self.nxsignal.attrs['axes'])
            axes = [None] * len(axis_names)
            for i, axis_name in enumerate(axis_names):
                axis_name = axis_name.strip()
                if axis_name == '' or axis_name == '.':
                    axes[i] = empty_axis(i)
                else:
                    axes[i] = plot_axis(self[axis_name])
            return axes
        except (AttributeError, IndexError, KeyError, UnboundLocalError):
            axes = {}
            for entry in self:
                if 'axis' in self[entry].attrs:
                    axis = self[entry].attrs['axis']
                    if axis not in axes and self[entry] is not self.nxsignal:
                        axes[axis] = self[entry]
                    else:
                        return None
            if axes:
                return [plot_axis(axes[axis]) for axis in sorted(axes)]
            elif self.nxsignal is not None:
                return [NXfield(np.arange(self.nxsignal.shape[i]), 
                        name='Axis%s'%i) for i in range(self.nxsignal.ndim)]
            return None

    @nxaxes.setter
    def nxaxes(self, axes):
        """
        Setter for the axes attribute.
        
        The argument should be a list of valid NXfields, which are added, if 
        necessary to the group. Values of None in the list denote missing axes. 
        """
        if not is_iterable(axes):
            axes = [axes]
        axes_attr = []
        for axis in axes:
            if axis is None:
                axes_attr.append('.')
            else:
                axes_attr.append(axis.nxname)
                if axis not in self:
                    self[axis.nxname] = axis
        self.attrs['axes'] = axes_attr

    @property
    def nxerrors(self):
        """
        Returns the NXfield containing the signal errors.
        """
        if self.nxsignal is not None: 
            if ('uncertainties' in self.nxsignal.attrs and
                self.nxsignal.attrs['uncertainties'] in self):
                return self[self.nxsignal.attrs['uncertainties']]
            elif self.nxsignal.nxname+'_errors' in self:
                return self[self.nxsignal.nxname+'_errors']
        try:
            return self['errors']
        except KeyError:
            return None

    @nxerrors.setter
    def nxerrors(self, errors):
        """
        Setter for the errors.
        
        The argument should be a valid NXfield.
        """
        if self.nxsignal is not None:
            name = self.nxsignal.nxname+'_errors'
            self.nxsignal.attrs['uncertainties'] = name
        else:
            name = 'errors'
        self[name] = errors
        return self.entries[name]

    @property
    def mask(self):
        """Returns the signal mask if one exists."""
        if self.nxsignal is not None:
            return self.nxsignal.mask
        else:
            return None

    @mask.setter
    def mask(self, value):
        """Sets a value for the signal mask if it exists.
        
        This can only be used with a value of np.ma.nomask to remove the mask.
        """
        if value is np.ma.nomask and self.nxsignal.mask is not None:
            self.nxsignal.mask = np.ma.nomask
            if isinstance(self.nxsignal.mask, NXfield):
                del self[self.nxsignal.mask.nxname]
            if 'mask' in self.nxsignal.attrs:
                del self.nxsignal.attrs['mask']


class NXmonitor(NXdata):

    """
    NXmonitor group. This is a subclass of the NXdata class.

    See the NXdata and NXgroup documentation for more details.
    """

    def __init__(self, signal=None, axes=None, *args, **kwargs):
        NXdata.__init__(self, signal=signal, axes=axes, *args, **kwargs)
        self._class = "NXmonitor"
        if "name" not in kwargs:
            self._name = "monitor"


class NXlog(NXgroup):

    """
    NXlog group. This is a subclass of the NXgroup class.

    See the NXgroup documentation for more details.
    """

    def __init__(self, *args, **kwargs):
        self._class = "NXlog"
        NXgroup.__init__(self, *args, **kwargs)

    def plot(self, **kwargs):
        """
        Plots the logged values against the elapsed time. Valid Matplotlib 
        parameters, specifying markers, colors, etc, can be specified using the 
        'kwargs' dictionary.
        """
        title = NXfield("%s Log" % self.nxname)
        if 'start' in self['time'].attrs:
            title = title + ' - starting at ' + self['time'].attrs['start']
        NXdata(self['value'], self['time'], title=title).plot(**kwargs)


class NXprocess(NXgroup):

    """
    NXprocess group. This is a subclass of the NXgroup class.

    See the NXgroup documentation for more details.
    """

    def __init__(self, *args, **kwargs):
        self._class = "NXprocess"
        NXgroup.__init__(self, *args, **kwargs)
        if "date" not in self:
            from datetime import datetime as dt
            self.date = dt.isoformat(dt.today())


class NXnote(NXgroup):

    """
    NXnote group. This is a subclass of the NXgroup class.

    See the NXgroup documentation for more details.
    """

    def __init__(self, *args, **kwargs):
        self._class = "NXnote"
        NXgroup.__init__(self, **kwargs)
        for arg in args:
            if is_text(arg):
                if "description" not in self:
                    self.description = arg
                elif "data" not in self:
                    self.data = arg
            elif isinstance(arg, NXobject):
                setattr(self, arg.nxname, arg)
            else:
                raise NeXusError(
                    "Non-keyword arguments must be valid NXobjects")
        if "date" not in self:
            from datetime import datetime as dt
            self.date = dt.isoformat(dt.today())


#-------------------------------------------------------------------------
#Add remaining base classes as subclasses of NXgroup and append to __all__

for cls in nxclasses:
    if cls not in globals():
        globals()[cls] = _makeclass(cls)
    __all__.append(cls)

#-------------------------------------------------------------------------
def is_real_slice(idx):
    def is_not_real(i):
        if ((isinstance(i.start, numbers.Integral) or i.start is None) and
               (isinstance(i.stop, numbers.Integral) or i.stop is None)):
            return True
        else:
            return False
    if idx is None or isinstance(idx, numbers.Integral):
        return False
    elif isinstance(idx, numbers.Real):
        return True
    elif isinstance(idx, slice):
        if is_not_real(idx):
            return False
        else:
            return True
    else:
        for ind in idx:
            if isinstance(ind, slice):
                if not is_not_real(ind):
                    return True
            elif ind is not None and not isinstance(ind, numbers.Integral):
                return True
        return False

def convert_index(idx, axis):
    """
    Converts floating point limits to a valid array index.
    
    This is for one-dimensional axes only. If the index is a tuple of slices, 
    i.e., for two or more dimensional data, the index is returned unchanged.
    """
    if is_real_slice(idx) and axis.ndim > 1: 
        raise NeXusError(
            "NXfield must be one-dimensional for floating point slices")
    elif is_iterable(idx) and len(idx) > axis.ndim:
        raise NeXusError("Slice dimension incompatible with NXfield")
    if axis.size == 1:
        idx = 0
    elif isinstance(idx, slice) and not is_real_slice(idx):
        if idx.start is not None and idx.stop is not None:
            if idx.stop == idx.start or idx.stop == idx.start + 1:
                idx = idx.start
    elif isinstance(idx, slice):
        if isinstance(idx.start, NXfield) and isinstance(idx.stop, NXfield):
            idx = slice(idx.start.nxdata, idx.stop.nxdata, idx.step)
        if (idx.start is not None and idx.stop is not None and
            ((axis.reversed and idx.start < idx.stop) or
             (not axis.reversed and idx.start > idx.stop))):
            idx = slice(idx.stop, idx.start, idx.step)
        if idx.start is None:
            start = None
        else:
            start = axis.index(idx.start)
        if idx.stop is None:
            stop = None
        else:
            stop = axis.index(idx.stop, max=True) + 1
        if start is None or stop is None:
            idx = slice(start, stop, idx.step)
        elif stop <= start+1 or np.isclose(idx.start, idx.stop):
            idx = start
        else:
            idx = slice(start, stop, idx.step)
    elif (not isinstance(idx, numbers.Integral) and
             isinstance(idx, numbers.Real)):
        idx = axis.index(idx)
    return idx

def centers(signal, axes):
    """
    Returns the centers of the axes.

    This works regardless if the axes contain bin boundaries or centers.
    """
    def findc(axis, dimlen):
        if axis.shape[0] == dimlen+1:
            return (axis.nxdata[:-1] + axis.nxdata[1:]) / 2
        else:
            assert axis.shape[0] == dimlen
            return axis.nxdata
    return [findc(a,signal.shape[i]) for i,a in enumerate(axes)]

def getlock():
    """Return the number of seconds before a lock acquisition times out.

    If the value is 0, file locking is disabled.
    
    Returns
    -------
    int
        Number of seconds before a lock acquisition times out.
    """
    return NX_LOCK
    
def setlock(value=10):
    """Initialize NeXus file locking.

    This creates a file with `.lock` appended to the NeXus file name.
    
    Parameters
    ----------
    value : int, optional
        Number of seconds before a lock acquisition times out, by default 10.
        If the value is set to 0, file locking is disabled.
    """
    global NX_LOCK
    NX_LOCK = int(value)

nxgetlock = getlock
nxsetlock = setlock

def getmemory():
    """
    Returns the memory limit for data arrays (in MB).
    """
    return NX_MEMORY

def setmemory(value):
    """
    Sets the memory limit for data arrays (in MB).
    """
    global NX_MEMORY
    NX_MEMORY = value

nxgetmemory = getmemory
nxsetmemory = setmemory

def getcompression():
    """
    Returns default compression filter.
    """
    return NX_COMPRESSION

def setcompression(value):
    """
    Sets default compression filter.
    """
    global NX_COMPRESSION
    if value == 'None':
        value = None
    NX_COMPRESSION = value

nxgetcompression = getcompression
nxsetcompression = setcompression

def getencoding():
    """
    Returns the default encoding for input strings (usually 'utf-8').
    """
    return NX_ENCODING

def setencoding(value):
    """
    Sets the default encoding for input strings (usually 'utf-8').
    """
    global NX_ENCODING
    NX_ENCODING = value

nxgetencoding = getencoding
nxsetencoding = setencoding

def getmaxsize():
    """
    Returns the default maximum size for arrays without using core memory.
    """
    return NX_MAXSIZE

def setmaxsize(value):
    """
    Sets the default maximum size for arrays without using core memory.
    """
    global NX_MAXSIZE
    NX_MAXSIZE = value

nxgetmaxsize = getmaxsize
nxsetmaxsize = setmaxsize

# File level operations
def load(filename, mode='r'):
    """
    Reads a NeXus file returning a tree of objects.

    This is aliased to 'nxload' because of potential name clashes with Numpy
    """
    with NXFile(filename, mode) as f:
        root = f.readfile()
    return root

nxload = load

def save(filename, group, mode='w', **kwargs):
    """
    Writes a NeXus file from a tree of objects.
    """
    if group.nxclass == "NXroot":
        root = group
    elif group.nxclass == "NXentry":
        root = NXroot(group)
    else:
        root = NXroot(NXentry(group))
    with NXFile(filename, mode, **kwargs) as f:
        f.writefile(root)
        f.close()
 
nxsave = save

def duplicate(input_file, output_file, mode='w-', **kwargs):
    with NXFile(input_file, 'r') as input, NXFile(output_file, mode) as output:
        output.copyfile(input, **kwargs)

nxduplicate = duplicate

def directory(filename):
    """
    Outputs contents of the named NeXus file.
    """
    root = load(filename)
    print(root.tree)

nxdir = directory


def demo(argv):
    """
    Processes a list of command line commands.

    'argv' should contain program name, command, arguments, where command is one
    of the following:
        copy fromfile.nxs tofile.nxs
        ls f1.nxs f2.nxs ...
    """
    if len(argv) > 1:
        op = argv[1]
    else:
        op = 'help'
    if op == 'ls':
        for f in argv[2:]: dir(f)
    elif op == 'copy' and len(argv)==4:
        tree = load(argv[2])
        save(argv[3], tree)
    elif op == 'plot' and len(argv)==4:
        tree = load(argv[2])
        for entry in argv[3].split('.'):
            tree = getattr(tree,entry)
        tree.plot()
        tree._plotter.show()

    else:
        usage = """
    usage: %s cmd [args]
    copy fromfile.nxs tofile.nxs
    ls *.nxs
    plot file.nxs entry.data
        """%(argv[0],)
        print(usage)

nxdemo = demo


if __name__ == "__main__":
    import sys
    nxdemo(sys.argv)
