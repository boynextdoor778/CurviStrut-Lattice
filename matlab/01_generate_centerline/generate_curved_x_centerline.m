function sample = generate_curved_x_centerline(nPtsPerArm, bendAmp, refAxis, radiusNorm)
%GENERATE_CURVED_X_CENTERLINE Generate one curved-X unit-cell centerline sample.
%
% Output sample fields:
%   nodeList      : shared topology node list, mainly for reference
%   strutList     : topology strut list, mainly for reference
%   strutPaths    : cell array, each cell is nPtsPerArm x 3 centerline points
%   radiusNorm    : strut radius normalized by unit-cell size
%   bendAmp       : curvature amplitude in normalized unit-cell coordinates
%   nPtsPerArm    : number of sampled centerline points per arm
%   refAxis       : global bending direction
%
% Coordinates are normalized to a unit cell [0,1]^3. Repetition and physical
% scaling are handled later by repeat/export scripts.

if nargin < 1 || isempty(nPtsPerArm); nPtsPerArm = 61; end
if nargin < 2 || isempty(bendAmp);    bendAmp = 0.08; end
if nargin < 3 || isempty(refAxis);    refAxis = [0 0 1]; end
if nargin < 4 || isempty(radiusNorm); radiusNorm = 0.035; end

validateattributes(nPtsPerArm, {'numeric'}, {'scalar','integer','>=',3});
validateattributes(bendAmp, {'numeric'}, {'scalar','>=',0});
validateattributes(refAxis, {'numeric'}, {'vector','numel',3});
validateattributes(radiusNorm, {'numeric'}, {'scalar','>',0});

bendDir = refAxis(:).';
if norm(bendDir) < 1e-12
    error('refAxis cannot be zero.');
end
bendDir = bendDir / norm(bendDir);

corners = [ ...
    0 0 0;
    1 1 1;
    1 0 0;
    0 1 1;
    0 1 0;
    1 0 1;
    1 1 0;
    0 0 1];

center = [0.5 0.5 0.5];
nodeList = center;
strutList = [];
strutPaths = cell(size(corners,1), 1);
centerID = 1;

for k = 1:size(corners,1)
    p0 = corners(k, :);
    p1 = center;

    pairSign = sign(dot(p0 - center, bendDir));
    if pairSign == 0
        pairSign = 1;
    end

    t = linspace(0, 1, nPtsPerArm).';
    P = p0 + t .* (p1 - p0);

    nWave = 2.0;
    env   = (sin(pi*t)).^2;
    wave  = sin(2*pi*nWave*t) .* env;
    P = P + pairSign * bendAmp * wave .* bendDir;

    strutPaths{k} = P;

    armIDs = zeros(nPtsPerArm, 1);
    for i = 1:nPtsPerArm-1
        nodeList(end+1, :) = P(i, :); %#ok<AGROW>
        armIDs(i) = size(nodeList, 1);
    end
    armIDs(end) = centerID;

    for i = 1:nPtsPerArm-1
        strutList(end+1, :) = [armIDs(i), armIDs(i+1)]; %#ok<AGROW>
    end
end

sample = struct();
sample.nodeList = nodeList;
sample.strutList = strutList;
sample.strutPaths = strutPaths;
sample.radiusNorm = radiusNorm;
sample.bendAmp = bendAmp;
sample.nPtsPerArm = nPtsPerArm;
sample.refAxis = bendDir;
sample.unitCellSize = [1 1 1];
end
