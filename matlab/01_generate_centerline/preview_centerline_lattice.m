function preview_centerline_lattice(strutPaths, pngFile, titleText)
%PREVIEW_CENTERLINE_LATTICE Save a quick centerline preview PNG.
if nargin < 3; titleText = ''; end
fig = figure('Visible','off', 'Color','w');
hold on;
for k = 1:numel(strutPaths)
    P = strutPaths{k};
    plot3(P(:,1), P(:,2), P(:,3), 'LineWidth', 2.0);
end
axis equal;
grid on;
xlabel('X'); ylabel('Y'); zlabel('Z');
view(35, 22);
title(titleText, 'Interpreter','none');
if nargin >= 2 && ~isempty(pngFile)
    exportgraphics(fig, pngFile, 'Resolution', 180);
end
close(fig);
end
