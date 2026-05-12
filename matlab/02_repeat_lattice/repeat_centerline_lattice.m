function repeatedPaths = repeat_centerline_lattice(strutPaths, repeatN)
%REPEAT_CENTERLINE_LATTICE Repeat unit-cell centerline paths in x/y/z.
% Coordinates are still normalized by unit-cell size after repetition.
% Example: repeatN=[2 2 2] gives coordinates in [0,2]x[0,2]x[0,2].

validateattributes(repeatN, {'numeric'}, {'vector','numel',3,'integer','>=',1});
repeatedPaths = {};
idx = 0;
for ix = 0:repeatN(1)-1
    for iy = 0:repeatN(2)-1
        for iz = 0:repeatN(3)-1
            shift = [ix iy iz];
            for k = 1:numel(strutPaths)
                idx = idx + 1;
                repeatedPaths{idx,1} = strutPaths{k} + shift; %#ok<AGROW>
            end
        end
    end
end
end
