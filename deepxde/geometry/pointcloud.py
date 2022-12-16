import numpy as np

from .geometry import Geometry
from .. import config
from ..data import BatchSampler


class PointCloud(Geometry):
    """A geometry represented by a point cloud, i.e., a set of points in space.

    Args:
        points: A 2-D NumPy array. If `boundary_points` is not provided, `points` can 
            include points both inside the geometry or on the boundary; if `boundary_points`
            is provided, `points` includes only points inside the geometry.
        boundary_points: A 2-D NumPy array.
        normals: A 2-D NumPy array.
    """

    def __init__(self, points, boundary_points=None, boundary_normals=None):
        self.points = np.asarray(points, dtype=config.real(np))
        self.num_points = len(points)
        if boundary_points is None:
            if boundary_normals is not None:
                raise ValueError(
                    "boundary_points must be provided to use boundary_normals"
                )
            self.boundary_points = boundary_points
            self.boundary_normals = boundary_normals
            self.all_points = self.points
        else:
            if boundary_normals is not None:
                if len(boundary_normals) != len(boundary_points):
                    raise ValueError(
                        "the shape of boundary_normals should be the same as boundary_points"
                    )
            self.boundary_normals = boundary_normals
            self.boundary_points = np.asarray(
                boundary_points, dtype=config.real(np)
            )
            self.num_boundary_points = len(boundary_points)
            self.all_points = np.vstack((self.points, self.boundary_points))
            self.boundary_sampler = BatchSampler(
                self.num_boundary_points, shuffle=True
            )
        super().__init__(
            len(points[0]),
            (
                np.amin(self.all_points, axis=0),
                np.amax(self.all_points, axis=0),
            ),
            np.inf,
        )
        self.sampler = BatchSampler(self.num_points, shuffle=True)

    def inside(self, x):
        return np.isclose((x[:, None, :] - self.points[None, :, :]), 0, atol=1e-6).all(axis=2).any(axis=1)

    def on_boundary(self, x):
        if self.boundary_points is None:
            raise ValueError(
                "boundary_points must be defined to sample the boundary"
            )
        return np.isclose((x[:, None, :] - self.boundary_points[None, :, :]), 0, atol=1e-6).all(axis=2).any(axis=1)

    def random_points(self, n, random="pseudo"):
        if n <= self.num_points:
            indices = self.sampler.get_next(n)
            return self.points[indices]

        x = np.tile(self.points, (n // self.num_points, 1))
        indices = self.sampler.get_next(n % self.num_points)
        return np.vstack((x, self.points[indices]))

    def random_boundary_points(self, n, random="pseudo"):
        if self.boundary_points is None:
            raise ValueError(
                "boundary_points must be defined to sample the boundary"
            )
        if n <= self.num_boundary_points:
            indices = self.boundary_sampler.get_next(n)
            return self.boundary_points[indices]

        x = np.tile(self.boundary_points, (n // self.num_boundary_points, 1))
        indices = self.boundary_sampler.get_next(n % self.num_boundary_points)
        return np.vstack((x, self.boundary_points[indices]))
