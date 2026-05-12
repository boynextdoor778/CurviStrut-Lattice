function [uniqueNodes, elementList] = merge_duplicate_centerline_nodes(strutPaths, tol)
%MERGE_DUPLICATE_CENTERLINE_NODES Convert paths into unique nodes and segment elements.
% This is useful for checking connectivity before Abaqus export.
if nargin < 2 || isempty(tol); tol = 1e-8; end

keyMap = containers.Map('KeyType','char','ValueType','double');
uniqueNodes = zeros(0,3);
elementList = zeros(0,2);

    function id = getNodeId(pt)
        key = sprintf('%d_%d_%d', round(pt(1)/tol), round(pt(2)/tol), round(pt(3)/tol));
        if isKey(keyMap, key)
            id = keyMap(key);
        else
            uniqueNodes(end+1,:) = pt; %#ok<AGROW>
            id = size(uniqueNodes,1);
            keyMap(key) = id;
        end
    end

for k = 1:numel(strutPaths)
    P = strutPaths{k};
    for i = 1:size(P,1)-1
        n1 = getNodeId(P(i,:));
        n2 = getNodeId(P(i+1,:));
        if n1 ~= n2
            elementList(end+1,:) = [n1 n2]; %#ok<AGROW>
        end
    end
end
end
