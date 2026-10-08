function numerical_write_json(filename,value)
% 完整写临时文件后替换索引/manifest；不用于覆盖原始求解记录。
folder=fileparts(filename); if ~isfolder(folder), mkdir(folder); end
temporary=[tempname(folder) '.json'];
fid=fopen(temporary,'w','n','UTF-8'); assert(fid>=0,'Cannot write %s.',temporary);
try
    fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true)); fclose(fid);
    [ok,message]=movefile(temporary,filename,'f'); assert(ok,'%s',message);
catch exception
    if fid>=0, try, fclose(fid); catch, end, end
    if isfile(temporary), delete(temporary); end
    rethrow(exception);
end
end
