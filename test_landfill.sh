#!/bin/bash

# TrackLab Landfill 测试脚本 - 一次一个脚本
# 使用方法: ./test_landfill.sh

echo "🧪 TrackLab Landfill 测试开始"
echo "==============================="

# 计数器
total=0
success=0
failed=0

# 测试结果日志
log_file="landfill_test_results.txt"
echo "TrackLab Landfill 测试结果 - $(date)" > $log_file
echo "===================================" >> $log_file

# 查找所有测试文件
echo "📁 查找测试文件..."
test_files=$(find landfill/functional_tests -name "*.py" | sort)

if [ -z "$test_files" ]; then
    echo "❌ 没有找到测试文件"
    exit 1
fi

echo "找到以下测试文件:"
echo "$test_files" | nl

echo ""
echo "开始逐个运行测试..."
echo ""

# 逐个运行测试
for test_file in $test_files; do
    total=$((total + 1))
    
    echo "----------------------------------------"
    echo "🧪 [$total] 测试: $test_file"
    echo "----------------------------------------"
    
    # 记录开始时间
    start_time=$(date +%s)
    
    # 运行测试 (激活tracklab环境)
    bash -c "eval \"\$(micromamba shell hook --shell bash)\" && micromamba activate tracklab && python '$test_file'" > temp_stdout.txt 2> temp_stderr.txt
    exit_code=$?
    
    # 记录结束时间
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    # 分析结果
    if [ $exit_code -eq 0 ]; then
        echo "✅ 成功 (${duration}s)"
        success=$((success + 1))
        echo "[$total] ✅ $test_file (${duration}s)" >> $log_file
    elif [ $exit_code -eq 1 ] && grep -q "ZeroDivisionError" temp_stderr.txt && [[ "$test_file" == *"t3_script_fail"* ]]; then
        echo "✅ 成功 - 预期错误 (${duration}s)"
        success=$((success + 1))
        echo "[$total] ✅ $test_file - 预期错误 (${duration}s)" >> $log_file
    else
        echo "❌ 失败 (退出码: $exit_code, ${duration}s)"
        failed=$((failed + 1))
        echo "[$total] ❌ $test_file (退出码: $exit_code, ${duration}s)" >> $log_file
        
        # 显示错误信息的前几行
        if [ -s temp_stderr.txt ]; then
            echo "错误信息:"
            head -n 3 temp_stderr.txt | sed 's/^/  /'
            echo ""
        fi
        
        # 保存详细错误信息到日志
        echo "    错误输出:" >> $log_file
        cat temp_stderr.txt | sed 's/^/      /' >> $log_file
        echo "" >> $log_file
    fi
    
    # 清理临时文件
    rm -f temp_stdout.txt temp_stderr.txt
    
    # 每10个测试显示进度
    if [ $((total % 10)) -eq 0 ]; then
        echo ""
        echo "📊 进度: $total 个测试完成 (成功: $success, 失败: $failed)"
        echo ""
    fi
done

echo ""
echo "==============================="
echo "📊 测试总结"
echo "==============================="
echo "总测试数: $total"
echo "✅ 成功: $success"
echo "❌ 失败: $failed"

if [ $total -gt 0 ]; then
    success_rate=$((success * 100 / total))
    echo "成功率: ${success_rate}%"
else
    echo "成功率: 0%"
fi

echo ""
echo "📄 详细结果已保存到: $log_file"

# 显示失败的测试
if [ $failed -gt 0 ]; then
    echo ""
    echo "❌ 失败的测试:"
    grep "❌" $log_file | head -10
    if [ $failed -gt 10 ]; then
        echo "   ... 还有 $((failed - 10)) 个失败测试 (查看 $log_file 获取完整列表)"
    fi
fi

echo ""
if [ $failed -eq 0 ]; then
    echo "🎉 所有测试都通过了！"
    exit 0
else
    echo "⚠️  有 $failed 个测试失败"
    exit 1
fi