# Component silhouettes and board envelope

The SVG preview now draws a dashed component-body silhouette for each component when `Mostrar referencias de componentes` / component display is enabled. The silhouette is estimated from the transformed extents of the component's actual pad geometry. It is deliberately dashed because the current GenCAD `$SHAPES` records contain pin placements but no authoritative package-body outline.

The preview also draws a dashed convex envelope around the available board geometry. This is an estimated extent, not a mechanical board perimeter. The supplied GenCAD `$BOARD` section contains paired circular artwork groups (204 groups across TOP/BOTTOM), not an explicit closed board-edge contour. The converter therefore does not claim this envelope is the true routed board outline. A true board edge requires a source mechanical outline / profile layer or a separate closed contour.

The PV data and source payload are unchanged. This affects only SVG visualization.
