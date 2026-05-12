function save_centerline_sample_mat(matFile, sample)
%SAVE_CENTERLINE_SAMPLE_MAT Save one centerline sample safely.
if ~isfield(sample, 'strutPaths')
    error('sample must contain strutPaths.');
end
save(matFile, '-struct', 'sample');
end
